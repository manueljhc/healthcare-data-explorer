# Prompt #1
I'd like to create a local prototype of an application that allows a user to use natural language to explore an existing healthcare database and answers questions like "what are the leading causes of mortality in ghana".

As input, the application should take:

- Postgres DB (SQLLite is okay for the prototype)
- User query

The application should employ several tools, developed using the Claude Agent SDK, to accomplish the following workflow:

1. Understand the database structure (discovery agent)
2. Interpret the users intent
3. Ask clarifying questions when needed
4. Generate & execute read-only SQL
5. Create visualizations & derive meaningful insights
6. Allow the user to re-prompt

Finally, the output should be:

- the SQL queries themselves
- an export button for the raw data
- a series of data visualizations (use plotly) chosen by the agent
- a summary of meaningful insights derived from those visuals

Throughout, we should employ several safety and security measures, including:

- only generate read-only SQL queries (e.g., no deletes or writes)
- allowing users to validate/iterate on queries
- limit row results and query execution time
- anything else you can think of?

Start by designing the architecture for this application.

# Prompt #2
Modify the app so the database discovery happens only once, and it creates an database disctionary artifact including database schema and summary of table headers/contents. This artifact should be referenced by the SQL executor, orchestrator, and prompts. It should also be visible to the end-user in the application, as an expandable "data dictionary" icon in the webapp.

# Prompt #3
Run the app and test it.

# Prompt #4
Commit all the changes.