# Dry run (no upload, logs payload)
python main.py --prompt 'Is AI conscious?' --dry-run

# Live mode (uploads to S3 + publishes to Instagram)
python main.py --prompt 'Is AI conscious?'