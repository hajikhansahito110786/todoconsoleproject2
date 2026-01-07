const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setSubmitting(true);
  setError('');

  try {
    // Prepare data with proper date format
    const todoData = {
      ...formData,
      student_id: formData.student_id || null,
      due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null
    };

    const response = await fetch('http://localhost:8000/todos/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(todoData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create todo');
    }

    router.push('/todos');
    router.refresh();
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to create todo');
    console.error('Create todo error:', err);
  } finally {
    setSubmitting(false);
  }
};