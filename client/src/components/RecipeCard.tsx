interface Ingredient {
  name: string
  quantity?: number
  unit?: string
  notes?: string
}

interface RecipeCardProps {
  id?: number
  uuid?: string
  title?: string
  description?: string
  ingredients?: Ingredient[]
  instructions?: string[]
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

export default function RecipeCard({ 
  id,
  uuid,
  title = 'Sample Recipe',
  description = 'A delicious recipe',
  ingredients = [],
  instructions = ['Step 1', 'Step 2'],
  prep_time_minutes,
  cook_time_minutes,
  total_time_minutes,
  servings,
  difficulty,
  cuisine_type,
  meal_type,
  dietary_tags,
  source_url,
  reddit_score,
  reddit_author,
  created_at,
  updated_at
}: RecipeCardProps) {
  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return null
    try {
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return null
    }
  }
  return (
    <div style={{
      border: '1px solid #ccc',
      borderRadius: '8px',
      padding: '1rem',
      margin: '1rem 0',
      textAlign: 'left'
    }}>
      <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>{title}</h2>
      
      {/* Metadata badges */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        flexWrap: 'wrap',
        marginBottom: '1rem'
      }}>
        {difficulty && (
          <span style={{
            padding: '0.25rem 0.5rem',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            backgroundColor: difficulty === 'easy' ? '#d4edda' : difficulty === 'medium' ? '#fff3cd' : '#f8d7da',
            color: difficulty === 'easy' ? '#155724' : difficulty === 'medium' ? '#856404' : '#721c24'
          }}>
            {difficulty.toUpperCase()}
          </span>
        )}
        {cuisine_type && (
          <span style={{
            padding: '0.25rem 0.5rem',
            borderRadius: '12px',
            fontSize: '0.75rem',
            backgroundColor: '#e7f3ff',
            color: '#004085'
          }}>
            🌍 {cuisine_type}
          </span>
        )}
        {meal_type && (
          <span style={{
            padding: '0.25rem 0.5rem',
            borderRadius: '12px',
            fontSize: '0.75rem',
            backgroundColor: '#fff4e6',
            color: '#663c00'
          }}>
            🍽️ {meal_type}
          </span>
        )}
        {dietary_tags && dietary_tags.map((tag, idx) => (
          <span key={idx} style={{
            padding: '0.25rem 0.5rem',
            borderRadius: '12px',
            fontSize: '0.75rem',
            backgroundColor: '#f0f0f0',
            color: '#333'
          }}>
            ✓ {tag}
          </span>
        ))}
      </div>

      {/* Time and serving info */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        marginBottom: '1rem',
        fontSize: '0.9rem',
        color: '#555'
      }}>
        {prep_time_minutes && (
          <div>⏲️ Prep: <strong>{prep_time_minutes}m</strong></div>
        )}
        {cook_time_minutes && (
          <div>🔥 Cook: <strong>{cook_time_minutes}m</strong></div>
        )}
        {total_time_minutes && (
          <div>⏱️ Total: <strong>{total_time_minutes}m</strong></div>
        )}
        {servings && (
          <div>🍴 Servings: <strong>{servings}</strong></div>
        )}
      </div>

      <p style={{ marginBottom: '1rem' }}>{description}</p>
      
      {/* IDs and source info */}
      <div style={{ 
        fontSize: '0.75rem', 
        color: '#888',
        marginBottom: '1rem',
        paddingBottom: '0.5rem',
        borderBottom: '1px solid #e0e0e0'
      }}>
        {uuid && <div style={{ fontFamily: 'monospace', marginBottom: '0.25rem' }}>UUID: {uuid}</div>}
        {id && <div>Recipe ID: {id}</div>}
        {created_at && (
          <div>📅 Created: <strong>{formatDate(created_at)}</strong></div>
        )}
        {updated_at && (
          <div>🔄 Updated: <strong>{formatDate(updated_at)}</strong></div>
        )}
        {reddit_author && (
          <div>👤 Reddit: <strong>{reddit_author}</strong> {reddit_score && `(${reddit_score} ⬆️)`}</div>
        )}
        {source_url && (
          <div>
            🔗 <a href={source_url} target="_blank" rel="noopener noreferrer" style={{ color: '#646cff' }}>
              Source
            </a>
          </div>
        )}
      </div>
      <h3>Ingredients</h3>
      <ul style={{ listStyle: 'none', paddingLeft: 0 }}>
        {ingredients.map((ingredient, index) => (
          <li key={index} style={{ 
            padding: '0.5rem 0',
            borderBottom: index < ingredients.length - 1 ? '1px solid #eee' : 'none'
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
              {(ingredient.quantity !== undefined && ingredient.quantity !== null) && (
                <span style={{ 
                  fontWeight: 'bold',
                  color: '#646cff',
                  minWidth: '3rem',
                  textAlign: 'right'
                }}>
                  {ingredient.quantity}
                </span>
              )}
              {ingredient.unit && (
                <span style={{ 
                  color: '#888',
                  minWidth: '3rem',
                  fontStyle: 'italic'
                }}>
                  {ingredient.unit}
                </span>
              )}
              <span style={{ flex: 1 }}>
                {ingredient.name}
              </span>
            </div>
            {ingredient.notes && (
              <div style={{ 
                fontSize: '0.85rem',
                color: '#666',
                marginTop: '0.25rem',
                marginLeft: '3.5rem',
                fontStyle: 'italic'
              }}>
                {ingredient.notes}
              </div>
            )}
          </li>
        ))}
      </ul>
      <h3>Instructions</h3>
      <ol>
        {instructions.map((instruction, index) => (
          <li key={index} style={{ marginBottom: '0.5rem' }}>{instruction}</li>
        ))}
      </ol>
    </div>
  )
}

