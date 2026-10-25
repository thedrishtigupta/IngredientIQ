# IngredientIQ Project Progress Document

## 1. Project Overview

IngredientIQ is an ingredient-aware beauty product recommendation system. It combines product metadata, structured ingredient information, ingredient-function knowledge, customer reviews, sentiment signals, and explainable ranking to help users find products for goals such as hydration, brightening, exfoliation, soothing, cleansing, UV protection, and hair conditioning.

The central design principle is that products are selected by structured data and deterministic scoring. The language model is used only to describe recommendations that have already been selected. It does not choose products, change their ranking, or introduce products that are not present in the database.

## 2. What Was Built Previously

The project previously established its data-processing and recommendation foundation. A product catalogue containing approximately 8,494 Sephora products was organized into a PostgreSQL data model. The database structure includes products, ingredients, product-ingredient relationships, ingredient knowledge, functional profiles, reviews, review summaries, and recommendation-related metadata.

The ingredient parser was built to handle the irregular formats found in real product labels. It supports nested parentheses, commas inside CI colour-code groups, `May Contain` sections, semicolon-delimited text, continuation fragments, product components, formulation steps, shade-specific sections, percentages, ingredient markers, and ingredient-name normalization. The parser preserves ingredient order and contextual information instead of treating every comma-separated value as an independent ingredient.

The data-profiling work identified the main quality characteristics of the catalogue. Most products contain ingredient information, but a meaningful subset does not. The profiling also identified duplicate products, multi-component products, missing values, and the limitations of treating raw ingredient text as a simple list. These findings were used to define the parser contract and the database representation.

The review data pipeline was also prepared. Review files were merged, cleaned, deduplicated, normalized, and summarized at product level. The processed review collection contains approximately 1.09 million reviews covering 2,351 products. Review summaries include counts, rating averages, recommendation rates, helpfulness information, review dates, and catalogue-comparison fields. This created the foundation for using review information in recommendation ranking.

The first recommendation engine was deterministic and ranked products using basic signals such as ingredient matching, product type, rating, popularity, category, subcategory, price, and ingredient filters. It supported user goals, category and subcategory selection, budget limits, required ingredients, excluded ingredients, and top-K results. Template-based explanations were generated from the recommendation evidence.

An initial frontend was also established. It provided the visual structure and user-facing pages for exploring products, viewing product information, comparing products, and viewing ingredient details. At this stage, however, the frontend used demonstration data and browser-side scoring rather than being connected to the live recommendation backend.

The project already included tests for the ingredient parser, parser edge cases, review-pipeline contracts, recommendation behavior, and explanation generation. These tests provided a baseline for safely extending the system.

## 3. What Is Built Now

The project now operates as an integrated recommendation application rather than a collection of separate data and prototype components.

### 3.1 Review Intelligence

Review text is now processed using VADER sentiment analysis. The system calculates average sentiment, positive and negative review shares, smoothed product-level review scores, and aspect-level signals for topics such as hydration, texture, scent, irritation, absorption, packaging, value, and effectiveness.

These signals are stored in the `product_review_signals` database table and can be used by the recommendation engine and product-detail views. Smoothing is applied so that products with only a small number of reviews are not treated as perfect or highly reliable based on very limited evidence. Products without review data are kept identifiable as having no review signal instead of being assigned fabricated review records.

### 3.2 Ingredient Vectors and Similarity

Products are now represented as vectors based on their ingredient-functional profiles. The vectors describe the functional jobs represented by a product’s ingredients, such as humectant, emollient, exfoliant, antioxidant, or other ingredient roles. User goals are represented as corresponding goal vectors.

Cosine similarity is used to measure how closely a product’s functional profile matches the requested goal. This extends the recommender beyond simple ingredient counting and allows products with related functional compositions to be compared.

### 3.3 Hybrid Recommendation Engine

The recommendation engine now combines six signals:

- Ingredient-goal matching
- Product-vector similarity
- Product-type intent
- Review sentiment
- Star rating
- Popularity

The current documented weighting is 30% ingredient match, 20% vector similarity, 15% product intent, 15% review sentiment, 12% rating, and 8% popularity. The engine applies hard filters before ranking products, so category, subcategory, price, required ingredients, and excluded ingredients are respected before scores are calculated.

The engine is deterministic. The same request and the same database state produce the same ranking. Ties are resolved consistently, and the final response includes component scores, matched goals, matched ingredients, review aspects, strengths, weaknesses, and the final hybrid score.

The recommender supports eleven documented user goals, including hydration, moisturization, brightening, exfoliation, antioxidant protection, soothing, oil control, UV protection, cleansing, barrier support, and hair conditioning.

### 3.4 LLM-Based Explanations

The LLM explanation layer is now connected through OpenRouter. After the deterministic engine selects the products, the system sends the product facts, shopper choices, matched ingredients, scores, and relevant review information to the language model.

The LLM generates short, plain-English explanations. Prompt rules restrict it to the facts supplied by the application, prevent unsupported medical claims, and limit ingredient references to ingredients that were actually matched by the recommender. If the API key is missing or the request fails, the system uses deterministic template explanations instead.

The API reports whether an explanation was actually generated by the LLM. This keeps the application transparent about the source of its text.

### 3.5 FastAPI Backend

The FastAPI backend now provides the application’s service layer. The main endpoints include:

- `POST /recommend` for ranked recommendations
- `GET /health` for service and database status
- `GET /goals` for supported recommendation goals
- `GET /categories` for categories and subcategories
- `GET /products` for product search
- `GET /products/{id}` for product details
- `GET /products/{id}/similar` for similar products
- `GET /ingredients` for ingredient search
- `GET /ingredients/{id}` for ingredient details

The API includes structured request and response schemas, validation errors, database-unavailable handling, product-not-found responses, CORS configuration for local frontend development, and interactive documentation through FastAPI’s `/docs` route.

### 3.6 Frontend Integration

The frontend is now connected to the real backend and database. The previous browser-side demonstration data and scoring logic have been replaced by API calls.

The Explore page allows users to select goals, categories, subcategories, price limits, fragrance preferences, required ingredients, excluded ingredients, and result limits. It displays live ranked products, score breakdowns, matched ingredients, review insights, and an explanation panel describing why a product was recommended.

The product, comparison, ingredient, home, and research routes have also been updated to consume the shared API layer. Loading, error, empty-result, and database-unavailable states are represented in the interface.

### 3.7 Database and Local Setup

The database can now be run through Docker using PostgreSQL 18. Setup and export scripts support restoring a shared database dump, initializing the local environment, checking table contents, and exporting a complete database snapshot.

This provides a repeatable local setup path and reduces the need for every developer to install and configure PostgreSQL manually. The database documentation explains the schema, restore process, dump requirements, local commands, and data relationships.

### 3.8 Testing and Evaluation

The test suite has expanded to cover the API, hybrid ranking, vectors, review sentiment, LLM behavior, parser behavior, explanation generation, and recommendation quality.

The evaluation process checks filtering rules, price constraints, excluded ingredients, required ingredients, duplicate prevention, deterministic ordering, score ranges, formula correctness, review-signal behavior, and top-K limits. The documented evaluation checks 279 request variations and thousands of returned products, with no rule violations in the recorded run.

The hybrid recommender also performs substantially better than simple ranking baselines for product-type precision. The evaluation shows that the system generally returns products of the appropriate type and products containing ingredients relevant to the selected goal. The evaluation documentation also records the limitations of these metrics and avoids presenting them as a substitute for human satisfaction measurements.

### 3.9 Project Documentation

The repository now contains a complete set of project documentation:

- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) for architecture and implementation handoff
- [WHAT_WAS_BUILT.md](./WHAT_WAS_BUILT.md) for a beginner-friendly explanation
- [API.md](./API.md) for endpoint behavior and examples
- [DATABASE.md](./DATABASE.md) for database setup and schema information
- [EVALUATION.md](./EVALUATION.md) for recommendation-quality results and limitations
- [VIVA_PREP.md](./VIVA_PREP.md) for project explanation and presentation preparation
- Data profiling, parser-contract, and review-pipeline documents under [data/](../data/)

## 4. Current Limitations

The current evaluation shows that review data is concentrated in Skincare. Other categories do not have equivalent review signals, which can create an imbalance when reviewed and unreviewed products are ranked together.

The `oil_control` goal can return makeup products such as eyeshadow, blush, and brow products when no category filter is supplied. This happens because some makeup products contain ingredients associated with oil control but do not necessarily match the intended product type.

Products without ingredient lists can pass some ingredient-related filters because missing information is not always treated as unknown. Required-ingredient matching is also based primarily on exact names, so chemically related names may not be grouped together. `May Contain` ingredients may also be treated as present even when they are optional.

The catalogue contains product variants, mini sizes, sets, and duplicate product families. These can appear together in recommendation results and may need product-family grouping or a clearer variant policy.

Ingredient knowledge covers only a subset of all catalogued ingredients. This limits the quality of goal matching and vector similarity for some goals. Similarity is also weaker for narrow goals where the available functional profile contains little relevant information.

The evaluation is primarily a plausibility and rule-compliance evaluation. It does not yet include human relevance labels, click data, purchase behavior, or long-term user feedback. Some evaluation metrics use the same curated ingredient knowledge that powers the recommender, so those metrics should be interpreted carefully.

The frontend still contains placeholder areas, including product imagery where the source dataset has no images and a research page that is not yet backed by a complete research-results workflow.

The local database configuration should also be made consistent across the Docker mapping, environment example, and written instructions so that all developers use the same host port.

## 5. Future Scope and Work Yet to Be Done

### 5.1 Recommendation Quality Improvements

The review component should be revised so that the existence of review data does not unintentionally provide a bonus to products in categories with better review coverage. Missing review data should be treated as genuinely neutral, or the review contribution should be centered around a representative value.

Product-intent rules should be refined for unlisted and unrelated subcategories. This is particularly important for oil-control recommendations, where makeup products can currently outrank more appropriate skincare products.

Ingredient filtering should distinguish between known absence and missing ingredient information. Products with no ingredient list should be clearly marked as unknown for fragrance-free and required-ingredient requests. Ingredient matching should also support aliases, normalized chemical names, related ingredient forms, and configurable handling of `May Contain` ingredients.

The catalogue should be normalized into product families so that full-size products, mini versions, sets, and duplicate variants can be handled according to a deliberate recommendation policy.

### 5.2 Ingredient Knowledge Expansion

The ingredient knowledge base should be expanded beyond its current curated subset. Additional functional groups, goals, ingredient roles, fragrance-related properties, colourant properties, and confidence metadata would improve both explainability and ranking quality.

The system should also support a controlled process for reviewing and updating ingredient knowledge rather than relying only on manual additions. New knowledge should be validated against parser output, product profiles, and recommendation behavior.

### 5.3 Research Angle

IngredientIQ can be extended from a recommendation application into a research platform for studying the relationship between product composition, consumer reviews, product popularity, and user goals.

One research direction is to investigate how ingredient composition relates to review sentiment, star ratings, recommendation rates, and review topics. This could include testing whether certain functional ingredient groups are associated with more positive or negative experiences, while carefully separating correlation from causation.

Another direction is to study ingredient effectiveness signals by comparing ingredient profiles with review-derived outcomes across product categories. The analysis could examine whether products with particular ingredients or functional combinations receive stronger sentiment for topics such as hydration, texture, absorption, irritation, scent, or effectiveness.

The project can also support research into explainable recommendation algorithms by comparing ingredient-only, hybrid, popularity-based, rating-based, and vector-similarity ranking methods. Future experiments could evaluate ranking stability, recommendation diversity, coverage across product categories, cold-start behavior, and the effect of different signal weights.

A further research direction is the development of human-labelled evaluation data. Beauty users or domain reviewers could assess whether a product is appropriate for a stated goal, whether an explanation is supported by the ingredient list, and whether the recommendation is useful. These labels would provide a less circular evaluation set than the current rule-based and knowledge-table-based metrics.

The research workflow should include statistical validation, confidence intervals, subgroup analysis, missing-data analysis, and careful documentation of dataset bias. It should avoid making medical or causal claims from review correlations alone. The system is suitable for product and recommendation research, not medical diagnosis or treatment advice.

The planned research page can eventually present these findings through charts, comparisons, ingredient associations, sentiment trends, and experiment summaries. It should be connected to reproducible analysis scripts and documented datasets rather than displaying manually entered results.

### 5.4 User Feedback and Personalization

The application should eventually capture anonymous user feedback such as useful/not-useful responses, selected products, filter usage, and explanation feedback. This data could support offline evaluation and later personalization while preserving privacy.

Future personalization could account for user preferences such as skin type, sensitivity, ingredient exclusions, budget, preferred brands, product format, and previous interactions. Any personalization layer should remain explainable and should not override explicit safety or ingredient constraints.

### 5.5 Frontend Completion

The frontend should replace placeholder imagery with reliable product-image handling when appropriate data becomes available. The research page should be completed as a real analysis interface, with clear separation between catalogue facts, review-derived observations, and experimental findings.

The interface should also make data limitations visible. For example, it should distinguish between “no reviews available,” “no ingredient list available,” and “no matching evidence found,” rather than presenting all three situations as equivalent.

### 5.6 Production Readiness

Before deployment, the project should receive a complete runtime validation pass covering database restoration, backend startup, frontend startup, API health, recommendation requests, product-detail requests, explanation fallbacks, and the main browser flow.

Production work should also include authentication or protected administrative access where needed, secret management, rate limiting for the LLM endpoint, structured logging, monitoring, database backup procedures, dependency security checks, and a deployment strategy for the frontend, API, and PostgreSQL database.

## 6. Overall Progress Summary

IngredientIQ has progressed from a data-processing and recommendation prototype into an integrated, explainable recommendation application. The project now has a structured ingredient pipeline, a populated relational database, review sentiment intelligence, vector similarity, hybrid ranking, LLM-assisted explanations, a FastAPI service, a live-data frontend, local Docker setup, automated tests, and a documented evaluation process.

The next stage is not to build the basic application from scratch. It is to improve recommendation fairness and data quality, complete the research and analytics direction, strengthen evaluation with human-labelled evidence, finish the remaining frontend areas, resolve configuration inconsistencies, and prepare the system for repeatable deployment and real-user validation.
