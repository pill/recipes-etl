import { useState } from 'react'
import RecipeCard from './RecipeCard'

interface Recipe {
  id?: number
  uuid?: string
  title: string
  description?: string
  ingredients: Array<{
    name: string
    quantity?: number
    unit?: string
    notes?: string
  }>
  instructions: string[]
  prep_time_minutes?: number
  cook_time_minutes?: number
  total_time_minutes?: number
  servings?: number
  difficulty?: string
  cuisine_type?: string
  meal_type?: string
  created_at?: string
  updated_at?: string
}

export default function RandomRecipe() {
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getRandomRecipe = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/recipes/_search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          size: 1,
          query: {
            function_score: {
              query: { match_all: {} },
              random_score: {},
            },
          },
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch recipe')
      }

      const data = await response.json()
      
      if (data.hits?.hits?.length > 0) {
        setRecipe(data.hits.hits[0]._source)
      } else {
        setError('No recipes found')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recipe')
      console.error('Error fetching recipe:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Random Recipe</h2>
      <button onClick={getRandomRecipe} disabled={loading}>
        {loading ? 'Loading...' : 'Get Random Recipe'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {recipe && (
        <RecipeCard
          id={recipe.id}
          uuid={recipe.uuid}
          title={recipe.title}
          description={recipe.description}
          ingredients={recipe.ingredients}
          instructions={recipe.instructions}
          prep_time_minutes={recipe.prep_time_minutes}
          cook_time_minutes={recipe.cook_time_minutes}
          total_time_minutes={recipe.total_time_minutes}
          servings={recipe.servings}
          difficulty={recipe.difficulty}
          cuisine_type={recipe.cuisine_type}
          meal_type={recipe.meal_type}
          created_at={recipe.created_at}
          updated_at={recipe.updated_at}
        />
      )}
    </div>
  )
}

