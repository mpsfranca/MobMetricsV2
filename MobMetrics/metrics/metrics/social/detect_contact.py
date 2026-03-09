import pandas as pd
from tqdm import tqdm

from ..utils.utils import distance
from ..utils.abs_metric import AbsMetric
from ...models import ContactModel, MetricsModel


class DetectContact(AbsMetric):
    """Detects contact events and updates contact-related metrics."""

    @staticmethod
    def extract(df, file_name, radius_threshold, contact_time_threshold, is_geo_coord):
        """Finds contacts, groups continuous events, and updates entity metrics."""
        contacts = DetectContact._find_contacts(df, file_name, radius_threshold, is_geo_coord)
        DetectContact._find_continuity(contacts, contact_time_threshold, file_name)
        DetectContact._contact_metrics(contacts, file_name)

    @staticmethod
    def _find_contacts(df, file_name, radius_threshold, is_geo_coord):
        """Identifies pairwise contacts at each timestamp."""
        unique_times = df["datetime"].unique()
        contact_records = []

        for t in tqdm(unique_times, desc="Processing contacts"):
            subset = df[df["datetime"] == t]

            if len(subset) < 2:
                continue

            objects = subset.to_dict(orient="records")

            for i in range(len(objects)):
                for j in range(i + 1, len(objects)):
                    obj1, obj2 = objects[i], objects[j]

                    dist = distance(obj1, obj2, is_geo_coord)

                    if dist < radius_threshold:
                        contact_records.append({
                            "file_name": file_name,
                            "id1": obj1["uid"],
                            "id2": obj2["uid"],
                            "contact_timestamp": t,
                        })

        return pd.DataFrame(contact_records)

    @staticmethod
    def _find_continuity(contacts, contact_time_threshold, file_name):
        """Groups consecutive contact observations into continuous contact events."""
        if contacts.empty:
            raise ValueError("No contacts found. Run _find_contacts() first.")

        contacts.sort_values(by=["id1", "id2", "contact_timestamp"], inplace=True)

        contact_instances = []
        prev_row = None
        start_timestamp = end_timestamp = None

        for _, row in contacts.iterrows():
            # Consecutive records for the same pair are merged into one contact event.
            if (
                prev_row is not None
                and row["id1"] == prev_row["id1"]
                and row["id2"] == prev_row["id2"]
                and (row["contact_timestamp"] - prev_row["contact_timestamp"]).total_seconds() <= contact_time_threshold
            ):
                end_timestamp = row["contact_timestamp"]
            else:
                if prev_row is not None:
                    contact_instances.append(ContactModel(
                        file_name=file_name,
                        id1=prev_row["id1"],
                        id2=prev_row["id2"],
                        initial_timestamp=start_timestamp,
                        final_timestamp=end_timestamp,
                        contact_time=(end_timestamp - start_timestamp).total_seconds(),
                    ))
                start_timestamp = row["contact_timestamp"]
                end_timestamp = row["contact_timestamp"]

            prev_row = row

        if prev_row is not None:
            contact_instances.append(ContactModel(
                file_name=file_name,
                id1=prev_row["id1"],
                id2=prev_row["id2"],
                initial_timestamp=start_timestamp,
                final_timestamp=end_timestamp,
                contact_time=(end_timestamp - start_timestamp).total_seconds(),
            ))

        ContactModel.objects.bulk_create(contact_instances)

    @staticmethod
    def _contact_metrics(contacts, file_name):
        """Updates per-entity contact metrics from the detected contact events."""
        for contact in contacts:
            id1 = contact.id1
            id2 = contact.id2
            contact_time = contact.contact_time

            ids = (id1, id2)

            for n in ids:
                metric = MetricsModel.objects.filter(file_name=file_name, uid=n).first()

                metric_total_contact_time = (metric.total_contact_time or 0) + contact_time
                metric_num_contacts = (metric.num_contacts or 0) + 1
                metric_avg_contact_time = metric_total_contact_time / metric_num_contacts

                metric.total_contact_time = metric_total_contact_time
                metric.num_contacts = metric_num_contacts
                metric.avg_contact_time = metric_avg_contact_time

                metric.save()
