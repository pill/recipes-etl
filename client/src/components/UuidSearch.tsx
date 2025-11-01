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
  dietary_tags?: string[]
  source_url?: string
  reddit_score?: number
  reddit_author?: string
}

export default function UuidSearch() {
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [uuidQuery, setUuidQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const searchByUuid = async () => {
    if (!uuidQuery.trim()) {
      setError('Please enter a UUID')
      return
    }

    setLoading(true)
    setError(null)
    setRecipe(null)
    
    try {
      const response = await fetch('/api/recipes/_search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: {
            term: {
              'uuid.keyword': uuidQuery.trim()
            }
          }
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to search recipe by UUID')
      }

      const data = await response.json()
      
      if (data.hits?.hits?.length > 0) {
        setRecipe(data.hits.hits[0]._source)
      } else {
        setError('No recipe found with that UUID')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search recipe by UUID')
      console.error('Error searching recipe by UUID:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setUuidQuery('')
    setRecipe(null)
    setError(null)
  }

  return (
    <div>
      <h2>Search by UUID</h2>
      <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Look up a specific recipe using its unique identifier (UUID)
      </p>
      
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input
          type="text"
          value={uuidQuery}
          onChange={(e) => setUuidQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && searchByUuid()}
          placeholder="e.g. 8faa4a5f-4f52-56db-92aa-fa574ed6b62c"
          style={{ 
            padding: '0.5rem',
            width: '400px',
            fontFamily: 'monospace',
            fontSize: '0.9rem'
          }}
        />
        <button 
          onClick={searchByUuid} 
          disabled={loading || !uuidQuery.trim()}
          style={{
            padding: '0.5rem 1rem',
            cursor: loading || !uuidQuery.trim() ? 'not-allowed' : 'pointer',
            opacity: loading || !uuidQuery.trim() ? 0.6 : 1
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
        {(recipe || error) && (
          <button 
            onClick={handleClear}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#f0f0f0',
              border: '1px solid #ccc',
              cursor: 'pointer'
            }}
          >
            Clear
          </button>
        )}
      </div>

      {error && (
        <div style={{ 
          padding: '1rem',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c33',
          marginBottom: '1rem'
        }}>
          ❌ {error}
        </div>
      )}

      {recipe && (
        <div>
          <div style={{
            padding: '0.75rem 1rem',
            backgroundColor: '#e7f3ff',
            border: '1px solid #b3d9ff',
            borderRadius: '4px',
            marginBottom: '1rem',
            fontSize: '0.9rem'
          }}>
            ✅ Recipe found! UUID: <code style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{recipe.uuid}</code>
          </div>
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
            dietary_tags={recipe.dietary_tags}
            source_url={recipe.source_url}
            reddit_score={recipe.reddit_score}
            reddit_author={recipe.reddit_author}
          />
        </div>
      )}

      {!recipe && !error && !loading && (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#888',
          border: '2px dashed #ddd',
          borderRadius: '8px',
          marginTop: '1rem'
        }}>
          <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔍</p>
          <p>Enter a UUID above to find a specific recipe</p>
          <div style={{ fontSize: '0.85rem', marginTop: '1rem', color: '#aaa' }}>
            <p><strong>Example UUIDs:</strong></p>
            <p style={{ fontFamily: 'monospace' }}>8faa4a5f-4f52-56db-92aa-fa574ed6b62c</p>
            <p style={{ fontFamily: 'monospace' }}>11088052-b7a5-566a-9422-9f9b85fa88cb</p>
          </div>
        </div>
      )}
    </div>
  )
}

