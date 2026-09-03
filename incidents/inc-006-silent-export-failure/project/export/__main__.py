import logging
import sys

from export.job import ExportJob
from export.sink import FileSink


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sink = FileSink("/export-share/customers.csv")
    result = ExportJob(sink).run()
    if result.success:
        print(f"export succeeded: {result.rows_exported} rows")
    else:
        print(f"export FAILED: {result.error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
