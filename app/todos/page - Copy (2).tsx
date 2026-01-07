// In the actions section of each todo card in app/todos/page.tsx
<div className="flex space-x-2 pt-4 border-t">
  <Link
    href={`/todos/${todo.id}/edit`}
    className="flex-1 px-4 py-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-lg hover:bg-blue-100 text-center"
  >
    Edit
  </Link>
  
  {todo.status !== 'done' && (
    <button
      onClick={() => handleMarkComplete(todo.id)}
      className="flex-1 px-4 py-2 bg-green-50 text-green-700 text-sm font-medium rounded-lg hover:bg-green-100"
    >
      Complete
    </button>
  )}
  
  <button
    onClick={() => handleDelete(todo.id)}
    className="flex-1 px-4 py-2 bg-red-50 text-red-700 text-sm font-medium rounded-lg hover:bg-red-100"
  >
    Delete
  </button>
</div>