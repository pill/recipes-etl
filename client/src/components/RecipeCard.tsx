interface Ingredient {
  name: string
  quantity?: number
  unit?: string
  notes?: string
}

interface RecipeCardProps {
  id?: number
  title?: string
  description?: string
  ingredients?: Ingredient[]
  instructions?: string[]
}

export default function RecipeCard({ 
  id,
  title = 'Sample Recipe',
  description = 'A delicious recipe',
  ingredients = [],
  instructions = ['Step 1', 'Step 2']
}: RecipeCardProps) {
  return (
    <div style={{
      border: '1px solid #ccc',
      borderRadius: '8px',
      padding: '1rem',
      margin: '1rem 0',
      textAlign: 'left'
    }}>
      <h2>{title}</h2>
      <p>{description}</p>
      <p>Recipe ID: {id}</p>
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

