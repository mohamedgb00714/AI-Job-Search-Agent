# AI Job Search Agent

An intelligent job search assistant that analyzes resumes and finds matching job opportunities across multiple platforms. This actor uses LangGraph and LangChain to provide personalized job recommendations based on skills, experience, and preferences.

## 🚀 Features

- Resume analysis and skill extraction
- Multi-platform job search (LinkedIn, Indeed, Dice)
- Intelligent job matching and ranking
- Personalized recommendations
- Structured JSON output
- Automated job filtering and scoring

## 💡 Use Cases

- **Job Search**: Find relevant job opportunities based on resume and preferences
- **Skills Analysis**: Extract and analyze skills from resumes
- **Career Guidance**: Get personalized recommendations for job search
- **Market Research**: Understand job market trends and requirements
- **Resume Enhancement**: Identify skill gaps based on job requirements

## 🔧 Input Parameters

| Field | Type | Description |
|-------|------|-------------|
| `resume` | String | The resume text to analyze |
| `location` | String | Preferred job location (default: "Remote") |
| `jobType` | String | Type of employment (e.g., "full-time", "contract") |
| `keywords` | String | Additional search keywords |
| `modelName` | String | LLM model to use (default: "gpt-4") |

## 📊 Output

The actor provides structured JSON output containing:

1. **Summary**
   - Overview of search results
   - Number of matching jobs
   - Key insights

2. **Jobs Array** (Top 5 matches)
   - Job title
   - Company name
   - Location
   - Salary information
   - Match score (0-1)
   - Application URL
   - Employment type
   - Job description

3. **Recommendations**
   - Next steps for the job seeker
   - Career development suggestions
   - Application strategies

## 📚 Example Usage

```javascript
{
    "resume": "Your resume text here...",
    "location": "San Francisco",
    "jobType": "full-time",
    "keywords": "machine learning, python",
    "modelName": "gpt-4"
}
```

Example output:
```json
{
    "summary": "Found 15 matching jobs in San Francisco area...",
    "jobs": [
        {
            "title": "Senior Data Scientist",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "salary": "$150,000 - $200,000",
            "match_score": 0.92,
            "url": "https://..."
        }
    ],
    "recommendations": [
        "Update your ML skills section",
        "Apply within 24 hours of posting",
        "Highlight cloud computing experience"
    ]
}
```

## 🛠️ Customization

The actor can be customized by:

1. Adding new job boards in `src/tools.py`
2. Modifying the matching algorithm
3. Adjusting output format and fields
4. Customizing search parameters

## 📈 Performance Features

- Efficient parallel job search across platforms
- Smart result deduplication
- Rate limiting and error handling
- Result caching for improved performance
- Limited to top 5 most relevant results

## 💬 Support

- [Discord Community](https://discord.com/invite/jyEM2PRvMU)
- [Documentation](https://docs.apify.com/)
- [Apify SDK Docs](https://docs.apify.com/sdk/python/)

## 🔗 Related Actors

- [LinkedIn Jobs Scraper](https://apify.com/krandiash/linkedin-jobs-scraper)
- [Indeed Scraper](https://apify.com/krandiash/indeed-scraper)
- [Dice.com Scraper](https://apify.com/mohamedgb00714/dicecom-job-scraper)

## 📝 License

MIT License
