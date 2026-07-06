import tempfile
import unittest
from pathlib import Path

from ad_scraper.cli import expand_keywords, group_jobs_for_platform_sessions
from ad_scraper.config import ScraperJob, load_jobs_from_config, slugify
from ad_scraper.logging_utils import RunLog, build_slot_report
from ad_scraper.runner import (
    card_key,
    file_name_for,
    filter_cards_for_job,
    keyword_matches,
    output_folder_for,
    text_matches_filter,
)


class CoreTests(unittest.TestCase):
    def test_slugify_uses_safe_lowercase_names(self):
        self.assertEqual(slugify("Face Wash + SPF"), "face_wash_spf")
        self.assertEqual(slugify(""), "all")

    def test_job_accepts_prd_brand_and_pincode_aliases(self):
        job = ScraperJob.from_mapping(
            {
                "platform": "swiggy",
                "keyword": "chips",
                "brand": "Lays",
                "pincode": "110001",
                "match_type": "phrase",
            }
        )
        self.assertEqual(job.platform, "swiggy_instamart")
        self.assertEqual(job.brand_filter, "Lays")
        self.assertEqual(job.city_pincode, "110001")
        self.assertEqual(job.match_type, "phrase")

    def test_keyword_matching_handles_broad_phrase_and_exact(self):
        card_text = "Parachute Advansed Rosemary Essential Oil 14 ml"
        self.assertTrue(keyword_matches(card_text, "essential oils", "broad"))
        self.assertTrue(keyword_matches(card_text, "rosemary essential oil", "phrase"))
        self.assertTrue(keyword_matches(card_text, "rosemary essential oil", "exact"))
        self.assertFalse(keyword_matches(card_text, "tea tree essential oil", "phrase"))

    def test_brand_filter_allows_plural_product_word(self):
        card_text = "Parachute Advansed Tea Tree Essential Oil 14 ml"
        self.assertTrue(text_matches_filter(card_text, "parachute oils"))

    def test_job_accepts_persistent_browser_options(self):
        job = ScraperJob.from_mapping(
            {
                "platform": "blinkit",
                "keyword": "essential oils",
                "pincode": "122001",
                "first_placement_only": True,
                "user_data_dir": "profiles/blinkit-edge",
                "browser_channel": "msedge",
                "login_wait_ms": 60000,
                "login_phone": "9999999999",
            }
        )
        self.assertTrue(job.first_placement_only)
        self.assertEqual(job.user_data_dir, Path("profiles/blinkit-edge"))
        self.assertEqual(job.browser_channel, "msedge")
        self.assertEqual(job.login_wait_ms, 60000)
        self.assertEqual(job.login_phone, "9999999999")

    def test_job_defaults_require_visible_ad_tags_and_three_scrolls(self):
        job = ScraperJob.from_mapping(
            {
                "platform": "blinkit",
                "keyword": "chips",
                "pincode": "110001",
            }
        )
        self.assertFalse(job.save_screen)
        self.assertFalse(job.allow_position_fallback)
        self.assertTrue(job.require_ad_tag)
        self.assertEqual(job.scroll_depth, 3)
        self.assertEqual(job.match_type, "none")

    def test_sponsored_card_does_not_need_keyword_words_in_title_by_default(self):
        job = ScraperJob(
            platform="blinkit",
            keyword="coconut milk shampoo",
            brand_filter="Parachute",
            city_pincode="122001",
        )
        cards = [
            {
                "text": "Parachute Advansed Protein Dandruff Protection Shampoo 170 ml ₹156 ADD Ad",
                "reason": "text",
            }
        ]
        self.assertEqual(filter_cards_for_job(cards, job), cards)

    def test_card_key_dedupes_same_sponsored_card_text(self):
        cards = [
            {"text": "Parachute Advansed Protein Dandruff Shampoo 170 ml Rs 156 ADD Ad"},
            {"text": "Parachute Advansed Protein Dandruff Shampoo 170 ml Rs 156 ADD Ad"},
        ]
        self.assertEqual(card_key(cards[0]), card_key(cards[1]))

    def test_category_label_brand_filter_does_not_block_sponsored_ads(self):
        self.assertTrue(text_matches_filter("Parachute Advansed Shampoo", "S&C"))

    def test_expand_keywords_accepts_repeated_and_comma_values(self):
        self.assertEqual(
            expand_keywords("essential oils", ["rosemary essential oil,tea tree essential oil"]),
            ["essential oils", "rosemary essential oil", "tea tree essential oil"],
        )

    def test_output_folder_and_file_name_match_timeline_pattern(self):
        job = ScraperJob(
            platform="blinkit",
            keyword="chips",
            brand_filter="Lays",
            city_pincode="110001",
            output_dir=Path("screenshots"),
        )
        self.assertEqual(output_folder_for(job, "2026-06-26_18-30-00"), Path("screenshots/blinkit/2026-06-26_18-30-00"))
        self.assertEqual(
            file_name_for(job, "2025-06-15_14-32-01", "ad_1"),
            "blinkit__chips__lays__2025-06-15_14-32-01__ad_1.png",
        )

    def test_group_jobs_reuses_platform_session_for_multiple_keywords(self):
        jobs = [
            ScraperJob(platform="blinkit", keyword="chips", brand_filter="lays", city_pincode="110001"),
            ScraperJob(platform="blinkit", keyword="namkeen", brand_filter="lays", city_pincode="110001"),
            ScraperJob(platform="zepto", keyword="coffee", brand_filter="", city_pincode="110001"),
        ]
        groups = group_jobs_for_platform_sessions(jobs)
        group_sizes = sorted(len(group) for group in groups)
        self.assertEqual(group_sizes, [1, 2])

    def test_slot_report_includes_result_and_ad_slots(self):
        log = RunLog(
            run_timestamp="2026-06-27_10-00-00",
            platform="blinkit",
            keyword="Rosemary oil",
            brand_filter="Parachute",
            city_pincode="122001",
            ad_placements=[
                {
                    "result_slot": 2,
                    "ad_slot": 1,
                    "screenshot_path": "screenshots/blinkit/example.png",
                }
            ],
        )
        report = build_slot_report([log])
        self.assertIn("Rosemary oil\tParachute\tcaptured\t2\t1", report)

    def test_summary_report_includes_titleized_keyword_and_ordinal_ad_slots(self):
        from ad_scraper.logging_utils import build_summary_report, ordinal
        log = RunLog(
            run_timestamp="2026-06-27_10-00-00",
            platform="zepto",
            keyword="Mustard oil",
            brand_filter="Saffola",
            city_pincode="122001",
            ad_placements=[
                {
                    "result_slot": 6,
                    "ad_slot": 4,
                    "screenshot_path": "screenshots/zepto/example.png",
                }
            ],
        )
        summary = build_summary_report([log])
        self.assertEqual(summary, "Mustard Oil - 4th ad slot\n")
        
        # Test grouping multiple slots for the same keyword
        log_grouped = RunLog(
            run_timestamp="2026-06-27_10-00-00",
            platform="zepto",
            keyword="Mustard oil",
            brand_filter="Saffola",
            city_pincode="122001",
            ad_placements=[
                {"ad_slot": 2},
                {"ad_slot": 3},
            ],
        )
        self.assertEqual(build_summary_report([log_grouped]), "Mustard Oil - 2nd and 3rd ad slots\n")
        
        self.assertEqual(ordinal(1), "1st")
        self.assertEqual(ordinal(2), "2nd")
        self.assertEqual(ordinal(3), "3rd")
        self.assertEqual(ordinal(4), "4th")
        self.assertEqual(ordinal(11), "11th")
        self.assertEqual(ordinal(12), "12th")
        self.assertEqual(ordinal(13), "13th")
        self.assertEqual(ordinal(22), "22nd")

    def test_load_json_batch_config(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "jobs.json"
            config.write_text(
                """
                {
                  "jobs": [
                    {"platform": "blinkit", "keyword": "chips", "brand": "lays", "pincode": "110001"}
                  ]
                }
                """,
                encoding="utf-8",
            )
            jobs = load_jobs_from_config(config)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].platform, "blinkit")

    def test_custom_parachute_card_filtering(self):
        essential_oil_card = {
            "text": "Parachute Advansed Rosemary Essential Oil 14 ml",
            "reason": "text",
        }
        enriched_oil_card = {
            "text": "Parachute Advansed Rosemary Enriched Coconut Hair Oil 200 ml",
            "reason": "text",
        }
        bhringraj_oil_card = {
            "text": "Parachute Advansed Bhringraj Hair Oil 200 ml",
            "reason": "text",
        }
        competitor_card = {
            "text": "Soulflower Rosemary Essential Oil 15 ml",
            "reason": "text",
        }
        all_cards = [essential_oil_card, enriched_oil_card, bhringraj_oil_card, competitor_card]

        # Case 1: Search "rosemary essential oil" for brand "Parachute"
        job_1 = ScraperJob(
            platform="blinkit",
            keyword="rosemary essential oil",
            brand_filter="Parachute",
            city_pincode="122001",
        )
        res_1 = filter_cards_for_job(all_cards, job_1)
        self.assertEqual(res_1, [essential_oil_card])

        # Case 2: Search "rosemary oil" for brand "Parachute"
        job_2 = ScraperJob(
            platform="blinkit",
            keyword="rosemary oil",
            brand_filter="Parachute",
            city_pincode="122001",
        )
        res_2 = filter_cards_for_job(all_cards, job_2)
        self.assertEqual(res_2, [enriched_oil_card])

        # Case 3: Search "bhringraj" or "bhringraj oil" for brand "Parachute"
        job_3 = ScraperJob(
            platform="blinkit",
            keyword="bhringraj",
            brand_filter="Parachute",
            city_pincode="122001",
        )
        res_3 = filter_cards_for_job(all_cards, job_3)
        self.assertEqual(res_3, [bhringraj_oil_card])

        # Case 4: Generic keyword "coconut oil" for brand "Parachute" matches any Parachute card
        job_4 = ScraperJob(
            platform="blinkit",
            keyword="coconut oil",
            brand_filter="Parachute",
            city_pincode="122001",
        )
        res_4 = filter_cards_for_job(all_cards, job_4)
        self.assertEqual(res_4, [essential_oil_card, enriched_oil_card, bhringraj_oil_card])

        # Case 5: Competitor keyword "soulflower" for brand "Parachute" matches any Parachute card
        job_5 = ScraperJob(
            platform="blinkit",
            keyword="soulflower",
            brand_filter="Parachute",
            city_pincode="122001",
        )
        res_5 = filter_cards_for_job(all_cards, job_5)
        self.assertEqual(res_5, [essential_oil_card, enriched_oil_card, bhringraj_oil_card])

    def test_apply_mobile_chrome(self):
        from ad_scraper.image_utils import apply_mobile_chrome
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            test_path = Path(directory) / "test_screen.png"
            # Create a mock 412x915 image
            img = Image.new("RGB", (412, 915), (255, 255, 255))
            img.save(test_path)
            
            # Apply decoration
            apply_mobile_chrome(test_path, "Shampoo")
            
            # Verify output
            self.assertTrue(test_path.exists())
            result_img = Image.open(test_path)
            self.assertEqual(result_img.size, (412, 915))
            # The bottom navigation bar is black, so check a pixel at the bottom center
            bottom_pixel = result_img.getpixel((206, 910))
            self.assertEqual(bottom_pixel, (0, 0, 0))


if __name__ == "__main__":
    unittest.main()

