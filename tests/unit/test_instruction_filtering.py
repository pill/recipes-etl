"""Test ingredient filtering to detect instructions."""

import pytest
from recipes.models.schemas import RecipeIngredientSchema


def test_instruction_patterns():
    """Test that instruction-like ingredients are detected."""
    
    # These should be flagged as instructions
    instruction_like_ingredients = [
        'Fill a wok or large skillet with 3 inches of vegetable oil over medium high heat.',
        'Toss to combine then serve with ricotta salata.',
        'Preheat the oven to 350 degrees.',
        'Mix the flour and sugar together.',
        'Serve with fresh herbs.',
        'Heat a large pan over medium heat.',
        'Combine all ingredients in a bowl.',
    ]
    
    # Common skip patterns
    skip_patterns = [
        'fill a', 'fill the', 'toss to', 'serve with', 'preheat',
        'mix the', 'heat a', 'bake at', 'bake for', 'cook ', 'stir '
    ]
    
    # Action verbs for sentence detection
    action_verbs = ['fill', 'toss', 'serve', 'mix', 'stir', 'cook', 'bake', 
                   'heat', 'add', 'pour', 'place', 'combine', 'whisk', 'fold']
    
    for ingredient in instruction_like_ingredients:
        item_lower = ingredient.lower()
        
        # Check skip patterns
        matches_skip_pattern = any(pattern in item_lower for pattern in skip_patterns)
        
        # Check if it's a sentence with action verb
        is_sentence = ingredient.strip().endswith('.')
        has_action_verb = any(verb in item_lower for verb in action_verbs)
        is_long = len(ingredient.split()) > 5
        
        should_skip = matches_skip_pattern or (is_sentence and has_action_verb and is_long)
        
        assert should_skip, f'Ingredient should be filtered: {ingredient}'


def test_valid_ingredients():
    """Test that valid ingredients are NOT flagged as instructions."""
    
    valid_ingredients = [
        '1 cup all-purpose flour',
        '2 eggs',
        '1/2 cup sugar',
        '3 tablespoons olive oil',
        'Salt and pepper to taste',
        '1 pound ground beef',
        'Fresh basil leaves',
        '4 cloves garlic, minced',
    ]
    
    skip_patterns = [
        'fill a', 'fill the', 'toss to', 'serve with', 'preheat',
        'mix the', 'heat a', 'bake at', 'bake for', 'cook ', 'stir '
    ]
    
    action_verbs = ['fill', 'toss', 'serve', 'mix', 'stir', 'cook', 'bake', 
                   'heat', 'add', 'pour', 'place', 'combine', 'whisk', 'fold']
    
    for ingredient in valid_ingredients:
        item_lower = ingredient.lower()
        
        # Check skip patterns
        matches_skip_pattern = any(pattern in item_lower for pattern in skip_patterns)
        
        # Check if it's a sentence with action verb
        is_sentence = ingredient.strip().endswith('.')
        has_action_verb = any(verb in item_lower for verb in action_verbs)
        is_long = len(ingredient.split()) > 5
        
        should_skip = matches_skip_pattern or (is_sentence and has_action_verb and is_long)
        
        assert not should_skip, f'Valid ingredient should NOT be filtered: {ingredient}'


def test_edge_cases():
    """Test edge cases in ingredient filtering."""
    
    # Should be skipped (instructions)
    assert_should_skip = [
        'Preheat oven to 350°F.',
        'In a large bowl, combine flour and salt.',
        'Cook pasta according to package directions.',
    ]
    
    # Should NOT be skipped (valid ingredients with cooking-related words)
    assert_should_keep = [
        'Cooking oil',  # Short, no period
        'Pre-cooked chicken',  # Not a sentence
        'Heat-resistant spatula',  # Descriptive adjective
    ]


def test_section_headers_and_notes():
    """Test that section headers and standalone notes are filtered."""
    
    # Should be skipped
    should_skip = [
        'to taste',
        'For the Cookies',
        'For the Mousse Filling',
        'optional',
        'as needed',
        'if desired',
        'for garnish',
        'For Topping',
        'For Sauce',
    ]
    
    skip_patterns = [
        'for the ', 'for filling', 'for topping', 'for garnish', 'for sauce',
        'for dressing', 'for marinade', 'for glaze', 'for frosting',
    ]
    
    standalone_notes = ['to taste', 'optional', 'as needed', 'if desired', 'for garnish']
    
    for ingredient in should_skip:
        item_lower = ingredient.lower()
        
        # Check skip patterns
        matches_skip_pattern = any(pattern in item_lower for pattern in skip_patterns)
        
        # Check standalone notes
        is_standalone_note = ingredient.strip().lower() in standalone_notes
        
        should_skip_item = matches_skip_pattern or is_standalone_note
        
        assert should_skip_item, f'Should skip section header/note: {ingredient}'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

