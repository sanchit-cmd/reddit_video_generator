import sys
import os

# Ensure the parent directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.scrape_comments import scrape_comments
import unittest
from unittest.mock import patch, MagicMock

class TestScrapeCommentsFiltering(unittest.TestCase):

    @patch('service.scrape_comments.requests.get')
    def test_filter_links_and_gifs(self, mock_get):
        # Mock Reddit JSON response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {}, # Post data
            {
                "data": {
                    "children": [
                        {
                            "kind": "t1",
                            "data": {
                                "id": "valid1",
                                "body": "This is a valid comment with enough length to pass the check.",
                                "author": "user1",
                                "score": 10
                            }
                        },
                        {
                            "kind": "t1",
                            "data": {
                                "id": "link1",
                                "body": "Check out this link: https://example.com/verylargecomment",
                                "author": "user2",
                                "score": 5
                            }
                        },
                        {
                            "kind": "t1",
                            "data": {
                                "id": "gif1",
                                "body": "![gif](giphy|somehash) Look at this GIF!",
                                "author": "user3",
                                "score": 20
                            }
                        },
                        {
                            "kind": "t1",
                            "data": {
                                "id": "short1",
                                "body": "Too short",
                                "author": "user4",
                                "score": 2
                            }
                        }
                    ]
                }
            }
        ]
        mock_get.return_value = mock_response

        # Call scrape_comments with limit=5
        comments = scrape_comments("dummy_url", limit=5, min_length=30, max_length=300)

        # Verify results
        # Only 'valid1' should be kept. 
        # 'link1' has a link.
        # 'gif1' has a gif.
        # 'short1' is too short.
        
        self.assertEqual(len(comments), 1, f"Expected 1 comment, got {len(comments)}")
        self.assertEqual(comments[0]['id'], 'valid1')
        print("✅ Filtering test passed: Correctly filtered links, GIFs, and short comments.")

if __name__ == "__main__":
    unittest.main()
