import os

SRC = r"C:\Users\Ankit Umadi\Downloads\firex-10G.log"
DST = r"C:\Users\Ankit Umadi\Documents\hack\data\sample_validation_100MB.log"
TARGET_BYTES = 100 * 1024 * 1024  # 100 MB
SEEK_OFFSET = 1024 * 1024 * 1024   # Skip first 1 GB of data!

print(f"Seeking to {SEEK_OFFSET / (1024**3):.1f} GB offset in raw log file to extract unseen test sample...")

os.makedirs(os.path.dirname(DST), exist_ok=True)

with open(SRC, "rb") as f_in:
    f_in.seek(SEEK_OFFSET)
    # Discard partial line
    f_in.readline()
    
    bytes_written = 0
    line_count = 0
    with open(DST, "wb") as f_out:
        for line in f_in:
            f_out.write(line)
            bytes_written += len(line)
            line_count += 1
            if bytes_written >= TARGET_BYTES:
                break

print(f"Extracted {line_count:,} lines ({bytes_written / (1024*1024):.2f} MB) to {DST}")
