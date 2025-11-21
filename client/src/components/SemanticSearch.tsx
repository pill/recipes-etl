import { useState, useEffect } from 'react'
import RecipeCard from './RecipeCard'
import Pagination from './Pagination'

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
  created_at?: string
  updated_at?: string
}

const PAGE_SIZE = 10

export default function SemanticSearch() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalHits, setTotalHits] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchMode, setSearchMode] = useState<'semantic' | 'hybrid'>('semantic')

  const semanticSearch = async (page: number = 1) => {
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    
    try {
      // For semantic search, we need to:
      // 1. Generate embedding for the query (done on backend)
      // 2. Use kNN search with that embedding
      
      const response = await fetch('/api/recipes/_search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: (page - 1) * PAGE_SIZE,
          size: PAGE_SIZE,
          // Pure semantic search using kNN
          knn: {
            field: 'embedding',
            query_vector: null, // Will be generated on backend from query text
            k: PAGE_SIZE,
            num_candidates: 100,
          },
          // Pass the query text so backend can generate embedding
          query_text: searchQuery,
          search_mode: searchMode,
          _source: ['id', 'uuid', 'title', 'description', 'ingredients', 'instructions', 
                   'prep_time_minutes', 'cook_time_minutes', 'total_time_minutes', 
                   'servings', 'difficulty', 'cuisine_type', 'meal_type', 'dietary_tags',
                   'source_url', 'reddit_score', 'reddit_author', 'created_at', 'updated_at'],
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to perform semantic search')
      }

      const data = await response.json()
      
      if (data.hits?.hits?.length > 0) {
        setRecipes(data.hits.hits.map((hit: { _source: Recipe }) => hit._source))
        setTotalHits(data.hits.total.value)
        setCurrentPage(page)
      } else {
        setRecipes([])
        setTotalHits(0)
        setError('No recipes found')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to perform semantic search')
      console.error('Error performing semantic search:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setCurrentPage(1)
    setTotalHits(0)
  }, [searchQuery, searchMode])

  const handlePageChange = (page: number) => {
    semanticSearch(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div>
      <h2>Semantic Search</h2>
      <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
        Find recipes by meaning, not just keywords. Try searching for concepts like "comfort food" or "healthy breakfast".
      </p>
      
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ marginBottom: '0.5rem' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && semanticSearch(1)}
            placeholder="Search by meaning (e.g., 'comfort food', 'healthy breakfast')..."
            style={{ 
              padding: '0.5rem',
              width: '400px',
              marginRight: '0.5rem',
            }}
          />
          <button onClick={() => semanticSearch(1)} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        <div style={{ marginTop: '0.5rem' }}>
          <label style={{ marginRight: '1rem' }}>
            <input
              type="radio"
              value="semantic"
              checked={searchMode === 'semantic'}
              onChange={(e) => setSearchMode(e.target.value as 'semantic' | 'hybrid')}
              style={{ marginRight: '0.25rem' }}
            />
            Semantic Only
          </label>
          <label>
            <input
              type="radio"
              value="hybrid"
              checked={searchMode === 'hybrid'}
              onChange={(e) => setSearchMode(e.target.value as 'semantic' | 'hybrid')}
              style={{ marginRight: '0.25rem' }}
            />
            Hybrid (Semantic + Text)
          </label>
        </div>
      </div>
      
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      {recipes.length > 0 && (
        <div>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            Found {totalHits} recipe{totalHits !== 1 ? 's' : ''}
          </p>
          <Pagination
            currentPage={currentPage}
            totalResults={totalHits}
            pageSize={PAGE_SIZE}
            onPageChange={handlePageChange}
          />
          {recipes.map((recipe, index) => (
            <RecipeCard
              key={index}
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
              created_at={recipe.created_at}
              updated_at={recipe.updated_at}
            />
          ))}
          <Pagination
            currentPage={currentPage}
            totalResults={totalHits}
            pageSize={PAGE_SIZE}
            onPageChange={handlePageChange}
          />
        </div>
      )}
    </div>
  )
}

