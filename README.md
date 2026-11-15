# Peta Bahasa Satgas Soedirman

Interactive 3D map of regional-language capability among Serdik of Satgas Soedirman (Grup 1, 2, 3), across 119 regencies/cities in Java.

**Status:** Preliminary mapping, data as of 15/11/2026, 13.00 WIB.
Prepared by **Risdikti** (Bagian Riset, Pendidikan, dan Teknologi), Senat P3MDI.

## What it shows

- Block height is the number of Serdik who speak a language or dialect whose speech area covers that regency.
- Four indicators: number of speakers, dominant dialect, fluent speakers, and dialect diversity. Each can be filtered by language.
- Click or pick a regency to fly the camera to it. A pulse marks the selection, and the side panel shows a breakdown per dialect and per language, with fluency levels.
- Responsive layout: one screen on desktop, stacked on phones.

Regions are **speech areas** of a language or dialect, not a Serdik's origin or domicile. One Serdik can count in many regencies. The data is aggregated, and no names are included.

## Files

| Path | Purpose |
|---|---|
| `index.html` | The built, self-contained page. Open it directly or serve it statically. |
| `src/template.html` | Page source with `__DATA__` and `__LOGO__` placeholders. |
| `src/data.json` | Aggregated per-regency data plus simplified geometry. |
| `assets/logo-p3mdi.png` | P3MDI Soedirman emblem. |
| `scripts/build.py` | Rebuilds `src/data.json` and `index.html` from the recap workbook. |

## Rebuilding with new data

```bash
pip install pandas openpyxl shapely
python scripts/build.py path/to/Rekap_Bahasa_Daerah.xlsx path/to/all_kabkota_ind.geojson
```

- The workbook needs the sheets `Master Anggota`, `Detail Bahasa` and `Referensi Wilayah Bahasa`. It holds personal data, so do not commit it.
- Speech areas are taken from `Referensi Wilayah Bahasa` and matched on language and dialect. The region columns in `Detail Bahasa` are not used, because 19 of its rows were shifted.
- Regency boundaries: `kota/all_kabkota_ind.geojson` from [eppofahmi/geojson-indonesia](https://github.com/eppofahmi/geojson-indonesia).

## Notes

- The reference maps general Bahasa Jawa only to example regencies, so some Javanese-speaking regencies (for example Jombang, Lamongan and Tuban) show as empty.
- Fluency labels are normalised to Fasih, Menengah, Dasar and Belum dicantumkan. Where a Serdik has several entries, the highest level is kept.
- Speech-area reference: [Peta Bahasa, Badan Bahasa 2017](https://repositori.kemendikdasmen.go.id/7191/1/Peta%20Bahasa%202017.compressed-min%20%28pdf.io%29.pdf).
- Built with three.js 0.160 (loaded from jsDelivr) and the Satgas Soedirman design system.
