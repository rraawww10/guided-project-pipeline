"""ep-recipes-list and ep-recipe-get. One test per criterion, asserting only it."""
from __future__ import annotations

from helpers import SEED_RECIPES


def titles(body: list[dict]) -> list[str]:
    return [recipe.get("title") for recipe in body]


def test_c_1_1_recipes_list_returns_200_with_the_eight_seed_recipes(api):
    """c-1-1: GET /api/recipes returns 200 with a JSON array of the 8 seed recipes."""
    response = api.get("/api/recipes")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list), f"expected a JSON array, got {type(body).__name__}"
    assert len(body) == 8, f"expected the 8 seed recipes, got {len(body)}"
    assert [recipe.get("id") for recipe in body] == [r["id"] for r in SEED_RECIPES]
    assert titles(body) == [r["title"] for r in SEED_RECIPES]


def test_c_1_2_recipes_list_holds_eight_objects_and_the_pasta_entry_in_full(api):
    """c-1-2: 8 objects, and the lemon-garlic-pasta entry has id
    lemon-garlic-pasta, title Lemon Garlic Pasta, tags quick and vegetarian,
    minutes 20 and serves 4."""
    body = api.get("/api/recipes").json()
    assert isinstance(body, list), f"expected a JSON array, got {type(body).__name__}"
    assert len(body) == 8, f"expected 8 objects, got {len(body)}"

    matches = [r for r in body if isinstance(r, dict) and r.get("id") == "lemon-garlic-pasta"]
    assert len(matches) == 1, f"expected one lemon-garlic-pasta entry, got {len(matches)}"
    pasta = matches[0]
    assert pasta["id"] == "lemon-garlic-pasta"
    assert pasta["title"] == "Lemon Garlic Pasta"
    assert pasta["tags"] == ["quick", "vegetarian"], f"tags read {pasta.get('tags')!r}"
    assert pasta["minutes"] == 20, f"minutes read {pasta.get('minutes')!r}"
    assert pasta["serves"] == 4, f"serves read {pasta.get('serves')!r}"


def test_c_2_1_query_filter_is_case_insensitive(api):
    """c-2-1: ?q=garlic and ?q=GARLIC each return 200 with the same 2 recipes,
    Lemon Garlic Pasta and Garlic Flatbread."""
    lower = api.get("/api/recipes", params={"q": "garlic"})
    upper = api.get("/api/recipes", params={"q": "GARLIC"})
    assert lower.status_code == 200, lower.text
    assert upper.status_code == 200, upper.text

    expected = ["Lemon Garlic Pasta", "Garlic Flatbread"]
    assert sorted(titles(lower.json())) == sorted(expected), titles(lower.json())
    assert sorted(titles(upper.json())) == sorted(expected), titles(upper.json())
    assert titles(lower.json()) == titles(upper.json()), "the two cases disagree"


def test_c_2_2_tag_filter_alone_and_together_with_the_query(api):
    """c-2-2: ?tag=baking returns the 2 baking recipes, Banana Bread and Garlic
    Flatbread, and ?q=garlic&tag=baking returns 1, Garlic Flatbread."""
    tagged = api.get("/api/recipes", params={"tag": "baking"})
    assert tagged.status_code == 200, tagged.text
    assert sorted(titles(tagged.json())) == ["Banana Bread", "Garlic Flatbread"], (
        titles(tagged.json())
    )

    both = api.get("/api/recipes", params={"q": "garlic", "tag": "baking"})
    assert both.status_code == 200, both.text
    assert titles(both.json()) == ["Garlic Flatbread"], titles(both.json())


def test_c_3_1_recipe_get_returns_200_with_the_stored_recipe(api):
    """c-3-1: GET /api/recipes/lemon-garlic-pasta returns 200 with that recipe,
    its 7 ingredients and its 4 steps."""
    response = api.get("/api/recipes/lemon-garlic-pasta")
    assert response.status_code == 200, f"got {response.status_code}: {response.text}"
    recipe = response.json()
    assert isinstance(recipe, dict), f"expected a JSON object, got {recipe!r}"
    assert recipe["id"] == "lemon-garlic-pasta"
    assert recipe["title"] == "Lemon Garlic Pasta"
    assert recipe["serves"] == 4
    assert len(recipe["ingredients"]) == 7, f"{len(recipe['ingredients'])} ingredients"
    assert len(recipe["steps"]) == 4, f"{len(recipe['steps'])} steps"


def test_c_3_2_recipe_get_returns_404_with_an_error_body_for_an_unknown_id(api):
    """c-3-2: GET /api/recipes/not-a-recipe returns 404 with a JSON body holding
    an error field."""
    response = api.get("/api/recipes/not-a-recipe")
    assert response.status_code == 404, f"got {response.status_code}: {response.text}"
    body = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {body!r}"
    assert "error" in body, f"no error field in {body!r}"
