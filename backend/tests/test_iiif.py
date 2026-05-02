import base64
import unittest

from fastapi import HTTPException

from app.main import iiif_manifest


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


if __name__ == "__main__":
    unittest.main()
