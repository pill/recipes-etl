import { useState, useEffect } from 'react'
import RecipeCard from './RecipeCard'
import Pagination from './Pagination'

interface Recipe {
  id?: number
  title: string
  description?: string
  ingredients: Array<{
    name: string
    quantity?: number
    unit?: string
    notes?: string
  }>
  instructions: string[]
}

const PAGE_SIZE = 10

export default function IngredientSearch() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [ingredient, setIngredient] = useState('')
  const [parsedIngredients, setParsedIngredients] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalHits, setTotalHits] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parseIngredients = (input: string): string[] => {
    return input
      .split(/[,;|\n]/)
      .map(ing => ing.trim())
      .filter(ing => ing.length > 0)
  }

  const parseBooleanQuery = (input: string): any => {
    // Parse complex boolean queries like: "chicken AND (garlic OR onion) AND cheese"
    const tokens = input.match(/\b(AND|OR|NOT)\b|\(|\)|[^()\s]+/g) || []
    
    if (tokens.length === 0) return null
    
    // Simple case: no boolean operators, just ingredients
    if (!tokens.some(token => ['AND', 'OR', 'NOT'].includes(token))) {
      const ingredients = parseIngredients(input)
      if (ingredients.length === 1) {
        // Single ingredient - use both wildcard and match for better results
        const ingredient = ingredients[0]
        return {
          nested: {
            path: 'ingredients',
            query: {
              bool: {
                should: [
                  // Exact match (highest priority)
                  { match: { 'ingredients.name': { query: ingredient, boost: 3 } } },
                  // Wildcard match (lower priority)
                  { wildcard: { 'ingredients.name': { value: `*${ingredient}*`, case_insensitive: true, boost: 2 } } },
                  // Partial word match (lowest priority)
                  { match: { 'ingredients.name': { query: ingredient, fuzziness: 'AUTO', boost: 1 } } }
                ],
                minimum_should_match: 1
              }
            }
          }
        }
      } else {
        // Multiple ingredients - use bool query with must (all ingredients required)
        return {
          bool: {
            must: ingredients.map(ing => ({
              nested: {
                path: 'ingredients',
                query: {
                  bool: {
                    should: [
                      { match: { 'ingredients.name': { query: ing, boost: 3 } } },
                      { wildcard: { 'ingredients.name': { value: `*${ing}*`, case_insensitive: true, boost: 2 } } },
                      { match: { 'ingredients.name': { query: ing, fuzziness: 'AUTO', boost: 1 } } }
                    ],
                    minimum_should_match: 1
                  }
                }
              }
            })),
          },
        }
      }
    }

    // Complex case: parse boolean expression
    return parseBooleanExpression(tokens)
  }

  const parseBooleanExpression = (tokens: string[]): any => {
    let i = 0
    
    const parseOr = (): any => {
      let left = parseAnd()
      
      while (i < tokens.length && tokens[i] === 'OR') {
        i++ // consume 'OR'
        const right = parseAnd()
        left = {
          bool: {
            should: [left, right],
            minimum_should_match: 1,
          },
        }
      }
      
      return left
    }

    const parseAnd = (): any => {
      let left = parseNot()
      
      while (i < tokens.length && tokens[i] === 'AND') {
        i++ // consume 'AND'
        const right = parseNot()
        left = {
          bool: {
            must: [left, right],
          },
        }
      }
      
      return left
    }

    const parseNot = (): any => {
      if (i < tokens.length && tokens[i] === 'NOT') {
        i++ // consume 'NOT'
        return {
          bool: {
            must_not: [parseTerm()],
          },
        }
      }
      return parseTerm()
    }

    const parseTerm = (): any => {
      if (i < tokens.length && tokens[i] === '(') {
        i++ // consume '('
        const result = parseOr()
        if (i < tokens.length && tokens[i] === ')') {
          i++ // consume ')'
        }
        return result
      }
      
      if (i < tokens.length) {
        const term = tokens[i++]
        return {
          nested: {
            path: 'ingredients',
            query: {
              bool: {
                should: [
                  { match: { 'ingredients.name': { query: term, boost: 3 } } },
                  { wildcard: { 'ingredients.name': { value: `*${term}*`, case_insensitive: true, boost: 2 } } },
                  { match: { 'ingredients.name': { query: term, fuzziness: 'AUTO', boost: 1 } } }
                ],
                minimum_should_match: 1
              }
            }
          }
        }
      }
      
      throw new Error('Unexpected end of expression')
    }

    return parseOr()
  }

  const searchByIngredient = async (page: number = 1) => {
    if (!ingredient.trim()) return

    setLoading(true)
    setError(null)
    
    try {
      const query = parseBooleanQuery(ingredient)
      
      if (!query) {
        setError('Invalid query format')
        setLoading(false)
        return
      }

      // Extract ingredients for display
      const ingredients = parseIngredients(ingredient)
      setParsedIngredients(ingredients)

      const response = await fetch('/api/recipes/_search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: (page - 1) * PAGE_SIZE,
          size: PAGE_SIZE,
          query,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to search by ingredient')
      }

      const data = await response.json()
      
      if (data.hits?.hits?.length > 0) {
        setRecipes(data.hits.hits.map((hit: any) => hit._source))
        setTotalHits(data.hits.total.value)
        setCurrentPage(page)
      } else {
        setRecipes([])
        setTotalHits(0)
        setError(`No recipes found matching query: ${ingredient}`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search by ingredient')
      console.error('Error searching by ingredient:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setCurrentPage(1)
    setTotalHits(0)
  }, [ingredient])

  const handlePageChange = (page: number) => {
    searchByIngredient(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div>
      <h2>Advanced Ingredient Search</h2>
      <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: '#888' }}>
        <p>Supports boolean operators: <strong>AND</strong>, <strong>OR</strong>, <strong>NOT</strong>, and parentheses for grouping.</p>
        <p>Examples: <code>chicken AND garlic</code> | <code>beef OR pork</code> | <code>(beef OR pork) AND onion</code></p>
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          value={ingredient}
          onChange={(e) => setIngredient(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && searchByIngredient(1)}
          placeholder="e.g. chicken AND garlic OR (beef AND onion)"
          style={{ 
            padding: '0.5rem',
            width: '400px',
            marginRight: '0.5rem',
          }}
        />
        <button onClick={() => searchByIngredient(1)} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {parsedIngredients.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: '#888' }}>
            Query: <code style={{ backgroundColor: 'rgba(255,255,255,0.1)', padding: '0.2rem 0.4rem', borderRadius: '3px' }}>{ingredient}</code>
          </p>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {parsedIngredients.map((ing, index) => (
              <span
                key={index}
                style={{
                  backgroundColor: 'rgba(100, 108, 255, 0.1)',
                  color: '#646cff',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '12px',
                  fontSize: '0.85rem',
                  border: '1px solid rgba(100, 108, 255, 0.2)'
                }}
              >
                {ing}
              </span>
            ))}
          </div>
        </div>
      )}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {recipes.length > 0 && (
        <div>
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
              title={recipe.title}
              description={recipe.description}
              ingredients={recipe.ingredients}
              instructions={recipe.instructions}
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

