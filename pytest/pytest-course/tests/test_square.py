import pytest
import source.shapes as shapes

@pytest.mark.parametrize("side_length, expected_area", [(5, 25), (4,16), (9,81)])
def test_multiple_sqaure_areas(side_length, expected_area):
    assert shapes.Square(side_length).area() == expected_area 
    
    
@pytest.mark.parametrize("side_input, excpected_perimeneter",[(3,12),(4,16),(5,20)])
def test_multipale_perimeters(side_input, excpected_perimeneter):
    assert shapes.Square(side_input).perimeter() == excpected_perimeneter
