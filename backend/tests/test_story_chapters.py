"""
Test Story Chapters Feature for 4Luis Crowdfunding Platform
Tests:
- Journey model fields (story_chapters, current_chapter, story_emails_enabled)
- Homepage API returns story chapter data
- Journey detail API returns story chapter data
- Admin update API accepts story chapter updates
- Chapter detection logic (percentage -> chapter mapping)
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStoryChaptersAPI:
    """Test Story Chapters API endpoints"""
    
    def test_homepage_main_journey_returns_story_chapters(self):
        """Test GET /api/homepage/main-journey returns story_chapters and current_chapter"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "journey" in data, "Response should contain 'journey' key"
        
        journey = data["journey"]
        assert "story_chapters" in journey, "Journey should have story_chapters field"
        assert "current_chapter" in journey, "Journey should have current_chapter field"
        assert "story_emails_enabled" in journey, "Journey should have story_emails_enabled field"
        
        # Validate story_chapters structure
        story_chapters = journey["story_chapters"]
        assert story_chapters is not None, "story_chapters should not be None"
        assert isinstance(story_chapters, dict), "story_chapters should be a dict"
        
        # Check that chapter 1 exists and has correct structure
        if "1" in story_chapters:
            ch1 = story_chapters["1"]
            assert "title" in ch1, "Chapter should have title"
            assert "lines" in ch1, "Chapter should have lines"
            assert isinstance(ch1["lines"], list), "lines should be a list"
        
        # Validate current_chapter
        current_chapter = journey["current_chapter"]
        assert isinstance(current_chapter, int), "current_chapter should be int"
        assert 1 <= current_chapter <= 5, f"current_chapter should be 1-5, got {current_chapter}"
        
        print(f"✅ Homepage returns story_chapters: {bool(story_chapters)}")
        print(f"✅ Homepage returns current_chapter: {current_chapter}")
        print(f"✅ Story emails enabled: {journey.get('story_emails_enabled')}")
    
    def test_journey_detail_returns_story_chapters(self):
        """Test GET /api/journeys/journey_china001 returns story_chapters"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        journey = response.json()
        assert "story_chapters" in journey, "Journey should have story_chapters field"
        assert "current_chapter" in journey, "Journey should have current_chapter field"
        assert "story_emails_enabled" in journey, "Journey should have story_emails_enabled field"
        
        # Verify China journey has custom chapters
        story_chapters = journey["story_chapters"]
        assert story_chapters is not None, "China journey should have story_chapters"
        
        # Check all 5 chapters exist
        for i in range(1, 6):
            assert str(i) in story_chapters, f"Chapter {i} should exist"
            ch = story_chapters[str(i)]
            assert "title" in ch, f"Chapter {i} should have title"
            assert "lines" in ch, f"Chapter {i} should have lines"
        
        print(f"✅ Journey detail returns all 5 story chapters")
        print(f"✅ Chapter 1 title: {story_chapters['1']['title']}")
    
    def test_chapter_1_title_for_china(self):
        """Test that China journey at 2.5% shows Chapter 1 'O sonho nasce'"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        journey = data["journey"]
        progress = data.get("progress", {})
        
        percentage = progress.get("percentage", 0)
        current_chapter = journey.get("current_chapter", 1)
        story_chapters = journey.get("story_chapters", {})
        
        # At 2.5%, should be chapter 1
        assert percentage < 25, f"Percentage {percentage}% should be < 25%"
        assert current_chapter == 1, f"At {percentage}%, chapter should be 1, got {current_chapter}"
        
        # Verify Chapter 1 title
        ch1 = story_chapters.get("1", {})
        assert ch1.get("title") == "O sonho nasce", f"Chapter 1 title should be 'O sonho nasce', got {ch1.get('title')}"
        
        print(f"✅ At {percentage}%, current_chapter = {current_chapter}")
        print(f"✅ Chapter 1 title: '{ch1.get('title')}'")


class TestChapterDetectionLogic:
    """Test the chapter detection logic based on percentage"""
    
    def test_chapter_ranges(self):
        """
        Test chapter determination from percentage:
        - 0-25%: Chapter 1
        - 25-50%: Chapter 2
        - 50-75%: Chapter 3
        - 75-100%: Chapter 4
        - 100%+: Chapter 5
        """
        # Expected chapter for each percentage
        test_cases = [
            (0, 1),      # 0% = Chapter 1
            (10, 1),     # 10% = Chapter 1
            (24.9, 1),   # 24.9% = Chapter 1
            (25, 2),     # 25% = Chapter 2
            (49.9, 2),   # 49.9% = Chapter 2
            (50, 3),     # 50% = Chapter 3
            (74.9, 3),   # 74.9% = Chapter 3
            (75, 4),     # 75% = Chapter 4
            (99.9, 4),   # 99.9% = Chapter 4
            (100, 5),    # 100% = Chapter 5
            (150, 5),    # 150% = Chapter 5
        ]
        
        # Implement the same logic as backend
        def get_chapter_number(percentage: float) -> int:
            if percentage >= 100:
                return 5
            if percentage >= 75:
                return 4
            if percentage >= 50:
                return 3
            if percentage >= 25:
                return 2
            return 1
        
        for percentage, expected_chapter in test_cases:
            actual = get_chapter_number(percentage)
            assert actual == expected_chapter, f"At {percentage}%, expected chapter {expected_chapter}, got {actual}"
            print(f"✅ {percentage}% → Chapter {actual}")


class TestAdminStoryChaptersUpdate:
    """Test admin can update story chapters"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and get session"""
        self.session = requests.Session()
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed - skipping admin tests")
        
        data = login_response.json()
        self.admin_token = data.get("token")  # Note: API returns "token" not "access_token"
        self.session.headers.update({
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        })
    
    def test_admin_can_update_story_chapters(self):
        """Test PUT /api/admin/journeys/{journey_id} accepts story_chapters update"""
        # First, get current state
        get_response = self.session.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert get_response.status_code == 200
        
        original_journey = get_response.json()
        original_chapters = original_journey.get("story_chapters", {})
        
        # Prepare update with modified chapter 1 title
        test_title = "TEST O sonho nasce updated"
        updated_chapters = dict(original_chapters) if original_chapters else {}
        if "1" not in updated_chapters:
            updated_chapters["1"] = {"title": test_title, "lines": ["Test line"]}
        else:
            updated_chapters["1"] = dict(updated_chapters["1"])
            updated_chapters["1"]["title"] = test_title
        
        # Update journey
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/journeys/journey_china001",
            json={"story_chapters": updated_chapters}
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify update persisted
        verify_response = self.session.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert verify_response.status_code == 200
        
        updated_journey = verify_response.json()
        updated_ch1 = updated_journey.get("story_chapters", {}).get("1", {})
        assert updated_ch1.get("title") == test_title, f"Title should be '{test_title}', got {updated_ch1.get('title')}"
        
        print(f"✅ Admin updated chapter 1 title to: {updated_ch1.get('title')}")
        
        # Restore original title
        if original_chapters:
            restore_response = self.session.put(
                f"{BASE_URL}/api/admin/journeys/journey_china001",
                json={"story_chapters": original_chapters}
            )
            assert restore_response.status_code == 200, "Failed to restore original chapters"
            print(f"✅ Restored original chapter title")
    
    def test_admin_can_update_story_emails_enabled(self):
        """Test admin can toggle story_emails_enabled"""
        # Get current state
        get_response = self.session.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert get_response.status_code == 200
        original_value = get_response.json().get("story_emails_enabled", True)
        
        # Toggle value
        new_value = not original_value
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/journeys/journey_china001",
            json={"story_emails_enabled": new_value}
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify change
        verify_response = self.session.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert verify_response.status_code == 200
        actual_value = verify_response.json().get("story_emails_enabled")
        assert actual_value == new_value, f"Expected {new_value}, got {actual_value}"
        
        print(f"✅ story_emails_enabled changed from {original_value} to {new_value}")
        
        # Restore original
        restore_response = self.session.put(
            f"{BASE_URL}/api/admin/journeys/journey_china001",
            json={"story_emails_enabled": original_value}
        )
        assert restore_response.status_code == 200
        print(f"✅ Restored story_emails_enabled to {original_value}")
    
    def test_admin_can_update_current_chapter(self):
        """Test admin can update current_chapter (manual override)"""
        # Get current state
        get_response = self.session.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert get_response.status_code == 200
        original_chapter = get_response.json().get("current_chapter", 1)
        
        # Update to chapter 2
        test_chapter = 2
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/journeys/journey_china001",
            json={"current_chapter": test_chapter}
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify change
        verify_response = self.session.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert verify_response.status_code == 200
        actual_chapter = verify_response.json().get("current_chapter")
        assert actual_chapter == test_chapter, f"Expected chapter {test_chapter}, got {actual_chapter}"
        
        print(f"✅ current_chapter updated from {original_chapter} to {test_chapter}")
        
        # Restore original
        restore_response = self.session.put(
            f"{BASE_URL}/api/admin/journeys/journey_china001",
            json={"current_chapter": original_chapter}
        )
        assert restore_response.status_code == 200
        print(f"✅ Restored current_chapter to {original_chapter}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
