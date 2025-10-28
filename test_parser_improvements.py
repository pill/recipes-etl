#!/usr/bin/env python3
"""Test script to verify parser improvements for the "Hunters Gravy with Brats" recipe."""

import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from recipes.services.ai_service import AIService
from recipes.models.schemas import RecipeSchema, RecipeIngredientSchema, RecipeInstructionSchema

def test_validation():
    """Test the validation and cleanup function."""
    
    # Create a recipe with the problematic data from the user's example
    problematic_recipe = RecipeSchema(
        title="Hunters Gravy with Brats",
        description=None,
        ingredients=[
            RecipeIngredientSchema(item="Bratwurts", amount="4", notes=None),
            RecipeIngredientSchema(item="Dunkel or dark beer of choice", amount="to taste", notes=None),
            RecipeIngredientSchema(item="cooked Bonetti egg pasta or pasta of choice", amount="10 oz", notes=None),
            RecipeIngredientSchema(item="Dijon Mustard", amount="to taste", notes=None),
            RecipeIngredientSchema(item="1/2 cups beef stock", amount="1", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="4oz pancetta", amount="to taste", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="1tsp whole grain mustard", amount="to taste", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="1/3rd cup heavy cream", amount="to taste", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="2/3rd cup diced shallots", amount="around 2 medium ones", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="Chives", amount="for garnish", notes=None),
            RecipeIngredientSchema(item="8oz portabella mushrooms", amount="to taste", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="flour", amount="2 tbsp", notes=None),
            RecipeIngredientSchema(item="1tbsp white wine", amount="dry Riesling preferred", notes=None),  # SWAPPED
            RecipeIngredientSchema(item="Worcester sauce", amount="1 tsp", notes=None),
            RecipeIngredientSchema(item="garlic minced", amount="3 cloves", notes=None),
            RecipeIngredientSchema(item="Salt and pepper to taste\n\n**Preparation*", amount="to taste", notes=None),  # BAD
            # These are instructions, not ingredients:
            RecipeIngredientSchema(
                item="Cook pancetta on medium heat until fat has rendered and it starts to crisp, add garlic, shallots, and mushrooms, and cook until shallots have browned and mushrooms are soft, about 10 minutes.",
                amount="to taste",
                notes=None
            ),
            RecipeIngredientSchema(
                item="Deglaze pan with white wine and cook for a minute. Sprinkle the flour over the entire mixture, stirring continuously, until the flour just starts to brown.",
                amount="to taste",
                notes=None
            ),
            RecipeIngredientSchema(
                item="Fix the plate with pasta, top with gravy and chives. Brats on the side with Dijon for serving.",
                amount="to taste",
                notes=None
            ),
        ],
        instructions=[
            RecipeInstructionSchema(
                step=1,
                title="Step 1",
                description="Cook pancetta on medium heat until fat has rendered and it starts to crisp, add garlic, shallots, and mushrooms, and cook until shallots have browned and mushrooms are soft, about 10 minutes."
            ),
            RecipeInstructionSchema(
                step=2,
                title="Step 2",
                description="Deglaze pan with white wine and cook for a minute. Sprinkle the flour over the entire mixture, stirring continuously, until the flour just starts to brown."
            ),
            RecipeInstructionSchema(
                step=3,
                title="Step 3",
                description="Add in the broth, Worcestershire sauce, and whole grain mustard, stirring to combine. Bring to a boil, then reduce the heat and simmer until it reaches a desired consistency. Finally, stir in the heavy cream and simmer for an additional 2-3 minutes, remove from heat, add salt and pepper to taste. Keep warm until ready to serve."
            ),
            RecipeInstructionSchema(
                step=4,
                title="Step 4",
                description="In a large covered skillet, pour beer until it's about an inch deep. Raise heat to medium and wait until liquid starts to simmer. Add brats and cover, until internal temp is 160 degrees. Set aside brats, pour out beer, then add a 2 tbsp of neutral oil, and heat on medium high. Sear the Brats on all sides, then set aside and cover with foil until ready to serve"
            ),
            RecipeInstructionSchema(
                step=5,
                title="Step 5",
                description="Fix the plate with pasta, top with gravy and chives. Brats on the side with Dijon for serving."
            ),
        ],
        prepTime=None,
        cookTime=None,
        chillTime=None,
        panSize=None,
        difficulty="medium",
        cuisine=None,
        mealType="dessert",  # WRONG - should be dinner
        dietaryTags=None
    )
    
    print("=" * 80)
    print("BEFORE VALIDATION")
    print("=" * 80)
    print(f"Title: {problematic_recipe.title}")
    print(f"Meal Type: {problematic_recipe.mealType}")
    print(f"Number of ingredients: {len(problematic_recipe.ingredients)}")
    print("\nProblematic ingredients:")
    for i, ing in enumerate(problematic_recipe.ingredients, 1):
        item_preview = ing.item[:60] + "..." if len(ing.item) > 60 else ing.item
        print(f"  {i}. item='{item_preview}', amount='{ing.amount}'")
    
    # Apply validation
    ai_service = AIService()
    cleaned_recipe = ai_service._validate_and_cleanup_recipe(problematic_recipe)
    
    print("\n" + "=" * 80)
    print("AFTER VALIDATION")
    print("=" * 80)
    print(f"Title: {cleaned_recipe.title}")
    print(f"Meal Type: {cleaned_recipe.mealType}")
    print(f"Number of ingredients: {len(cleaned_recipe.ingredients)}")
    print("\nCleaned ingredients:")
    for i, ing in enumerate(cleaned_recipe.ingredients, 1):
        print(f"  {i}. item='{ing.item}', amount='{ing.amount}'")
    
    # Validation checks
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    issues_found = []
    issues_fixed = []
    
    # Check meal type
    if problematic_recipe.mealType == "dessert":
        issues_found.append("Meal type was incorrectly 'dessert'")
    if cleaned_recipe.mealType == "dinner":
        issues_fixed.append("✓ Meal type corrected to 'dinner'")
    else:
        print(f"✗ Meal type still incorrect: {cleaned_recipe.mealType}")
    
    # Check for instructions in ingredients
    instruction_count_before = sum(
        1 for ing in problematic_recipe.ingredients 
        if any(verb in ing.item.lower()[:10] for verb in ['cook', 'deglaze', 'fix'])
    )
    instruction_count_after = sum(
        1 for ing in cleaned_recipe.ingredients 
        if any(verb in ing.item.lower()[:10] for verb in ['cook', 'deglaze', 'fix'])
    )
    
    if instruction_count_before > 0:
        issues_found.append(f"Found {instruction_count_before} instructions in ingredients")
    if instruction_count_after == 0:
        issues_fixed.append(f"✓ Removed {instruction_count_before} instructions from ingredients")
    else:
        print(f"✗ Still has {instruction_count_after} instructions in ingredients")
    
    # Check for swapped fields
    swapped_before = sum(
        1 for ing in problematic_recipe.ingredients
        if ing.item and len(ing.item) > 0 and ing.item[0].isdigit()
    )
    swapped_after = sum(
        1 for ing in cleaned_recipe.ingredients
        if ing.item and len(ing.item) > 0 and ing.item[0].isdigit()
    )
    
    if swapped_before > 0:
        issues_found.append(f"Found {swapped_before} ingredients with swapped amount/item")
    if swapped_after < swapped_before:
        issues_fixed.append(f"✓ Fixed {swapped_before - swapped_after} swapped amount/item fields")
    
    # Check for markdown artifacts
    markdown_before = sum(
        1 for ing in problematic_recipe.ingredients
        if '**' in ing.item or '\n\n' in ing.item
    )
    markdown_after = sum(
        1 for ing in cleaned_recipe.ingredients
        if '**' in ing.item or '\n\n' in ing.item
    )
    
    if markdown_before > 0:
        issues_found.append(f"Found {markdown_before} ingredients with markdown artifacts")
    if markdown_after == 0:
        issues_fixed.append(f"✓ Removed markdown artifacts from ingredients")
    
    print("\nIssues found in original recipe:")
    for issue in issues_found:
        print(f"  • {issue}")
    
    print("\nIssues fixed by validation:")
    for fix in issues_fixed:
        print(f"  {fix}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_issues = len(issues_found)
    total_fixed = len(issues_fixed)
    print(f"Total issues found: {total_issues}")
    print(f"Total issues fixed: {total_fixed}")
    
    if total_fixed == total_issues and total_issues > 0:
        print("\n✅ All issues have been fixed!")
        return True
    elif total_fixed > 0:
        print(f"\n⚠️  Partially fixed: {total_fixed}/{total_issues} issues resolved")
        return True
    else:
        print("\n❌ No issues were fixed")
        return False

if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)

