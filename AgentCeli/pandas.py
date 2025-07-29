"""Minimal pandas stub with DataFrame from_dict and to_csv."""
import csv

class DataFrame:
    def __init__(self, data):
        self.data = data

    @classmethod
    def from_dict(cls, data, orient='columns'):
        return cls(data)

    def to_csv(self, path):
        if isinstance(self.data, dict) and self.data:
            header = list(next(iter(self.data.values())).keys())
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['key'] + header)
                for key, row in self.data.items():
                    writer.writerow([key] + [row.get(h, '') for h in header])
        else:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                for row in self.data:
                    writer.writerow(row)
