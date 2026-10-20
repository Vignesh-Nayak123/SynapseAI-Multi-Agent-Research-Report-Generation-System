import pytest
from src.tools.pdf import PDFProcessor

def test_validate_segment():
    processor = PDFProcessor()
    
    # Good segment
    good_text = "This is a valid text segment with reasonable density. It contains words and sentences."
    assert processor._validate_segment(good_text) is True
    
    # Bad segment (low density)
    bad_text = ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ."
    assert processor._validate_segment(bad_text) is False
    
    # Short segment
    short_text = "Too short"
    assert processor._validate_segment(short_text) is False
