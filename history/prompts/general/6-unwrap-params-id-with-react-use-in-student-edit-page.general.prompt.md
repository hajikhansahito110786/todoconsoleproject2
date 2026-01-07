---
id: 6
title: Unwrap params.id with React.use() in Student Edit Page
stage: bug fix
date_iso: 2026-01-06
surface: agent
model: gemini-1.5-pro
feature: none
branch: main
user: user
command:
  - "replace D:\\aa-w\\tododswithsqlmodelneon5withfrontendnextjs\\app\\students\[id]\\edit\\page.tsx"
labels:
  - bugfix
  - nextjs
  - client-component
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml:
  - app/students/[id]/edit/page.tsx
tests_yaml: []
prompt_text: |
  Console ErrorA param property was accessed directly with `params.id`. `params` is a Promise and must be unwrapped with `React.use()` before accessing its properties. Learn more: https://nextjs.org/docs/messages/sync-dynamic-apisapp/students/[id]/edit/page.tsx (12:37) @ EditStudentPage  10 |   const router = useRouter();  11 |   const queryClient = useQueryClient();> 12 |   const studentId = parseInt(params.id, 10);     |                                     ^  13 |  14 |   const [formData, setFormData] = useState({ nameplz: '', email: '' });  15 |
response_text: |
  I've applied the fix to `app/students/[id]/edit/page.tsx` by using `React.use(params.id)` to unwrap the `params.id` Promise, as indicated by the console error.

  **Please restart your Next.js frontend development server now** for this change to take effect.

  After restarting, please try accessing `http://localhost:3000/students/1/edit` and `http://localhost:3000/students/2/edit` again.

  Then, provide any new output from both your Next.js frontend console and your FastAPI backend console. We need to see if the frontend error is resolved and if the backend's debug print statement shows a student being found.
outcome: Applied React.use() fix for params.id and requested user to restart server and provide logs.
evaluation: The reported error was a clear Next.js usage issue. The fix was applied directly according to the error message's suggestion. The next step correctly instructs the user to restart the server and provide logs to verify the fix and continue debugging the "student not found" message.
---