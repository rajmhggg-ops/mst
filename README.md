# MST — Server OCR Final

This version moves OCR from the Android browser to a Python/Tesseract server.

## Flow
Gallery/Files → upload → server OCR → detected text → Auto Match → edit → download.

## Deploy
Use a Docker-capable HTTPS host such as Render. The included `Dockerfile` installs Tesseract automatically. After deployment, open the HTTPS URL on the phone.

## Local
`docker build -t mst .`
`docker run -p 8080:8080 mst`

Then open `http://localhost:8080`.

## Notes
- Upload accepts JPG, PNG and WebP, max 12 MB.
- ₹ quick-insert and OCR normalization are included.
- Font matching is visual estimation; a flattened image cannot reveal the original font file.
- Intended for ordinary photos, posters, designs, mockups and demo images.
