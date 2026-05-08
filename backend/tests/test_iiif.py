import base64
import unittest

from fastapi import HTTPException

from app.main import _append_generated_iiif_manifest, iiif_manifest


def _token(url):
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


class IiifEndpointTest(unittest.TestCase):
    def test_manifest_wraps_trusted_source_image(self):
        source_url = (
            "https://teylers.adlibhosting.com/ais6/Content/GetContent"
            "?command=getcontent&server=images&value=TvB%20G%200263.jpg"
            "&folderId=1&width=800&height=800&imageformat=jpg"
        )

        manifest = iiif_manifest(_token(source_url), label="Soldaat")

        self.assertEqual(manifest["@context"], "http://iiif.io/api/presentation/3/context.json")
        self.assertEqual(manifest["type"], "Manifest")
        self.assertEqual(manifest["label"]["none"], ["Soldaat"])
        body = manifest["items"][0]["items"][0]["items"][0]["body"]
        self.assertEqual(body["type"], "Image")
        self.assertTrue(body["id"].startswith("http://localhost:8000/iiif/image/"))

    def test_manifest_rejects_untrusted_image_host(self):
        with self.assertRaises(HTTPException) as exc:
            iiif_manifest(_token("https://example.org/image.jpg"))
        self.assertEqual(exc.exception.status_code, 403)

    def test_appends_manifest_for_boerhaave_image_representation(self):
        record = {
            "type": "HumanMadeObject",
            "_label": "Oudste telefoon van Nederland",
            "representation": [
                {
                    "type": "VisualItem",
                    "digitally_shown_by": [
                        {
                            "type": "DigitalObject",
                            "format": "image/jpeg",
                            "access_point": [
                                {
                                    "id": (
                                        "https://mmb-web.adlibhosting.com/ais6/webapi/wwwopac.ashx"
                                        "?command=getcontent&server=images"
                                        "&value=voorwerpen\\8200\\V08218-TH.JPG"
                                        "&folderId=2&width=800&height=800&imageformat=jpg"
                                    ),
                                    "type": "DigitalObject",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        _append_generated_iiif_manifest(record)

        manifest = record["subject_of"][0]["digitally_carried_by"][0]
        self.assertEqual(manifest["conforms_to"][0]["id"], "http://iiif.io/api/presentation/3/context.json")
        self.assertIn("/iiif/manifest/", manifest["access_point"][0]["id"])
        self.assertIn("Oudste%20telefoon%20van%20Nederland", manifest["access_point"][0]["id"])

    def test_does_not_duplicate_existing_manifest(self):
        record = {
            "type": "HumanMadeObject",
            "subject_of": [
                {
                    "type": "LinguisticObject",
                    "digitally_carried_by": [
                        {
                            "type": "DigitalObject",
                            "conforms_to": [
                                {"id": "http://iiif.io/api/presentation/3/context.json"}
                            ],
                        }
                    ],
                }
            ],
            "representation": [
                {
                    "type": "VisualItem",
                    "digitally_shown_by": [
                        {
                            "type": "DigitalObject",
                            "access_point": [
                                {
                                    "id": "https://mmb-web.adlibhosting.com/ais6/webapi/image.jpg",
                                    "type": "DigitalObject",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        _append_generated_iiif_manifest(record)

        self.assertEqual(len(record["subject_of"]), 1)


if __name__ == "__main__":
    unittest.main()
