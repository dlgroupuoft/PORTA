# Retained Source-Built Images

## Archive

- File: `qualified-cve-source-images.tar.gz`
- Size: 5.4 GB
- Contents: 27 vulnerable, fixed, and environment image tags for the eleven qualified CVEs
- Manifest: `qualified-cve-source-images.manifest`
- Checksum: `qualified-cve-source-images.tar.gz.sha256`

Verify and load from `broker/fuzzer`:

```bash
sha256sum -c Recall/Results/images/qualified-cve-source-images.tar.gz.sha256
gzip -dc Recall/Results/images/qualified-cve-source-images.tar.gz | docker load
```

The archive should be distributed through release storage or object storage, not normal Git history. Every target can also be rebuilt from the retained Dockerfile and source reference.

Regenerate the archive with:

```bash
Recall/Results/generation/save-qualified-images.sh
```
