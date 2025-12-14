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

# Promt #5

Add unit tests for the tools

# Prompt #6

I'd like to implement some user feedback. Let's start with the webapp UI, specifally the left hand side bar.

1. the database overview does not need to be pinned on the LHS menu bar. Instead make it a button with a collapsible pop up. Retain the export functionality.
2. Make the LHS less wide.

There are a couple design issues with the core chat workflow too.

1. In the case of multiple SQL queries, only one is displayed in the main chat interface. All queries should be visible.
2. When you start a conversation from the chat bar, the question is not displayed in the UI until the response finishes generating.
3. The following markdown did not render properly: "years to provide context:## Key Findings:"
4. The visualize button doesn't actually create visualizations.

# Prompt #7

The following SQL query caused a " I encountered an error: 'chart_type'". Please resolve it.

SELECT
country,
disease,
year,
month,
confirmed_cases,
suspected_cases,
incidence_per_100k,
outbreak_status
FROM infectious_disease_surveillance
WHERE country = 'Thailand'
AND disease = 'Yellow fever'
ORDER BY year DESC, month DESC LIMIT 10000

# Prompt #8

Tool use rejected with user message: You should fix this by creating more general logic, such that chart type is actually defined for this query, instead of just handling the error more elegantly. I suspect the issue here might be that the suggest charts tool is not recognizing that the time series data with multiple dimensions returned by the query is perfect for a line graph or scatter plot.

# Prompt #9

A good data analyst finds points of comparison (e.g., a baseline) when conducting analysis. This baseline might be constructed using an aggregation of historical data from the country in question - or similar countries - depending on the context of the question. Modify the system prompt such that answers are always contextualized in this way.

# Prompt #10

The agent should use per capita metrics where reasonable, especially when comparing across countries or time periods.