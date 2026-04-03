# AI-Powered Analysis with PII Protection

## Overview

The CV-Job Comparator now includes **AI-powered analysis** using Anthropic's Claude AI. This feature provides deeper insights, including strengths, weaknesses, cultural fit assessment, and detailed hiring recommendations.

**🔒 PRIVACY FIRST**: All personal identifiable information (PII) is automatically masked before sending data to the AI engine.

## Features

### 🤖 AI-Powered Analysis

When you enable AI analysis, you get:

1. **Detailed Assessments**: In-depth analysis of experience, skills, and certifications
2. **Candidate Strengths**: List of key strengths and competitive advantages
3. **Areas for Improvement**: Constructive feedback on gaps and weaknesses
4. **Hiring Recommendation**: Clear hire/consider/reject recommendation with reasoning
5. **Cultural Fit**: Assessment of how well the candidate fits the company culture
6. **Growth Potential**: Evaluation of the candidate's potential for development

### 🔒 Automatic PII Protection

Before sending your CV to the AI, the system **automatically masks**:

- ✅ **Name** (first line of CV)
- ✅ **Email addresses** (all formats)
- ✅ **Phone numbers** (all formats)
- ✅ **Physical addresses** (street addresses)
- ✅ **Age** (explicit mentions)
- ✅ **Date of birth** (DOB)
- ✅ **Social Security Numbers** (SSN)

### Example of PII Masking

**Original CV:**
```
John Smith
Email: john.smith@email.com
Phone: (555) 123-4567
Address: 123 Main Street, New York, NY 10001
Age: 32

Senior Software Engineer with 8 years of experience...
```

**Sent to AI:**
```
[NAME REDACTED]
Email: [EMAIL REDACTED]
Phone: [PHONE REDACTED]
Address: [ADDRESS REDACTED]
Age: [AGE REDACTED]

Senior Software Engineer with 8 years of experience...
```

## How to Use

### Step 1: Enable AI Analysis

1. Check the **"Use AI-Powered Analysis"** checkbox
2. An API key field will appear

### Step 2: Get Your Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

### Step 3: Enter Your API Key

1. Paste your API key in the provided field
2. The key is:
   - ✅ Never stored in the code
   - ✅ Never saved in the database
   - ✅ Used only for this single analysis
   - ✅ Transmitted securely over HTTPS

### Step 4: Run Analysis

1. Upload your CV (PDF, DOCX, or TXT)
2. Paste the job URL
3. Click "Analyze Match"
4. Wait 10-20 seconds for AI analysis

### Step 5: Review Results

You'll receive:
- Standard match scores (Experience, Skills, Certifications)
- AI-generated detailed assessments
- Strengths and weaknesses
- Hiring recommendation
- Cultural fit assessment
- Growth potential evaluation
- Privacy report (what PII was masked)

## API Key Security

### ✅ What We Do

- API key is only used for the current request
- Key is never logged or stored
- Key is transmitted over HTTPS only
- Key is cleared from memory after use

### ❌ What We Don't Do

- We never store your API key
- We never share your API key
- We never log your API key
- We never include it in error messages

### Best Practices

1. **Don't share your API key** with others
2. **Rotate keys regularly** in Anthropic Console
3. **Use separate keys** for different applications
4. **Revoke old keys** when no longer needed
5. **Monitor usage** in Anthropic Console

## Privacy Protection Details

### What Gets Masked

| PII Type | Pattern Matched | Example | Masked As |
|----------|----------------|---------|-----------|
| Name | First line of CV | John Smith | [NAME REDACTED] |
| Email | Standard email format | john@email.com | [EMAIL REDACTED] |
| Phone | Various formats | (555) 123-4567 | [PHONE REDACTED] |
| Address | Street addresses | 123 Main St | [ADDRESS REDACTED] |
| Age | "Age: X" or "Aged X" | Age: 32 | [AGE REDACTED] |
| DOB | Date formats | DOB: 01/15/1990 | [DOB REDACTED] |
| SSN | XXX-XX-XXXX | 123-45-6789 | [SSN REDACTED] |

### What Remains

The following information is **preserved** because it's needed for analysis:

- ✅ Work experience descriptions
- ✅ Skills and technologies
- ✅ Certifications and qualifications
- ✅ Education details
- ✅ Job titles and roles
- ✅ Company names (but not addresses)
- ✅ Projects and achievements

### Verification

After analysis, you'll see a **Privacy Report** showing:
- How many instances of each PII type were found
- Confirmation that all were masked
- Total number of redactions made

Example:
```
✅ Personal information was automatically protected:
• name: 1 instance(s) masked
• email: 2 instance(s) masked
• phone: 1 instance(s) masked
• address: 1 instance(s) masked
```

## Cost Considerations

### Anthropic API Pricing

AI analysis uses Claude Sonnet 4, which costs:
- **Input**: ~$3 per million tokens
- **Output**: ~$15 per million tokens

### Typical Usage

For a standard CV-job comparison:
- **Input tokens**: ~2,000-5,000 tokens (CV + job spec)
- **Output tokens**: ~1,000-2,000 tokens (analysis)
- **Estimated cost**: $0.02-$0.10 per analysis

### Tips to Minimize Costs

1. Use AI analysis only when needed
2. Use standard analysis for initial screening
3. Reserve AI for promising candidates
4. Set budget alerts in Anthropic Console
5. Monitor usage regularly

## Comparison: Standard vs AI Analysis

| Feature | Standard Analysis | AI Analysis |
|---------|------------------|-------------|
| **Speed** | 2-5 seconds | 10-20 seconds |
| **Cost** | Free | ~$0.02-$0.10 per analysis |
| **Match Scores** | ✅ Yes | ✅ Yes |
| **Skill Detection** | Pattern matching | ✅ AI understanding |
| **Experience Analysis** | Years only | ✅ Detailed assessment |
| **Strengths** | ❌ No | ✅ Yes |
| **Weaknesses** | ❌ No | ✅ Yes |
| **Recommendation** | ❌ No | ✅ Yes |
| **Cultural Fit** | ❌ No | ✅ Yes |
| **Growth Potential** | ❌ No | ✅ Yes |
| **PII Protection** | N/A | ✅ Automatic |
| **API Key Required** | ❌ No | ✅ Yes |

## When to Use AI Analysis

### ✅ Good Use Cases

- **Final round candidates**: Deep analysis for top contenders
- **Senior positions**: Need detailed cultural fit assessment
- **Borderline candidates**: When you need more insight
- **Complex roles**: Positions requiring nuanced evaluation
- **Team fit**: When cultural alignment is critical

### ❌ When Standard Analysis is Sufficient

- **Initial screening**: Large volume of applications
- **Junior positions**: Clear requirements
- **High volume**: Processing many CVs quickly
- **Budget constraints**: Free alternative available
- **Quick checks**: Simple yes/no decisions

## Troubleshooting

### "Invalid Anthropic API key format"

**Problem**: API key doesn't start with `sk-ant-`

**Solution**: 
- Check you copied the complete key
- Get a new key from Anthropic Console
- Make sure you're using an Anthropic key (not OpenAI)

### "Authentication error"

**Problem**: API key is invalid or expired

**Solution**:
- Verify key is active in Anthropic Console
- Check for typos in the pasted key
- Generate a new API key
- Ensure account has credits

### "AI analysis failed"

**Possible causes**:
1. Network timeout
2. API rate limit exceeded
3. Invalid response format
4. Service temporarily unavailable

**Solutions**:
- Wait a few seconds and try again
- Check Anthropic status page
- Verify account has sufficient credits
- Try with a smaller CV file

### No PII masked but expected

**Possible reasons**:
1. PII is in unusual format
2. Scanned PDF (OCR issues)
3. Non-standard formatting

**What to do**:
- Review the masked CV manually
- Manually redact sensitive info if needed
- Use a text-based CV for best results

## API Response Format

The AI returns a structured JSON response:

```json
{
  "overall_match": 85,
  "experience_analysis": {
    "score": 90,
    "required_years": 5,
    "candidate_years": 7,
    "assessment": "Candidate exceeds minimum requirements..."
  },
  "skills_analysis": {
    "score": 80,
    "required_skills": ["Python", "React", "AWS"],
    "matched_skills": ["Python", "React"],
    "missing_skills": ["AWS"],
    "additional_skills": ["Docker", "Kubernetes"],
    "assessment": "Strong technical foundation..."
  },
  "certifications_analysis": {
    "score": 100,
    "required_certifications": ["AWS Certified"],
    "matched_certifications": ["AWS Certified"],
    "missing_certifications": [],
    "assessment": "All required certifications present"
  },
  "strengths": [
    "Strong Python expertise",
    "Leadership experience",
    "Excellent communication"
  ],
  "weaknesses": [
    "Limited AWS experience",
    "No cloud certifications"
  ],
  "recommendation": "Strong hire - candidate shows...",
  "cultural_fit": "Collaborative style aligns well...",
  "growth_potential": "High potential for advancement...",
  "pii_masked": {
    "name": 1,
    "email": 2,
    "phone": 1,
    "address": 1
  }
}
```

## Privacy Policy

### Data Handling

1. **CV Text**: Sent to Anthropic API with PII masked
2. **Job Spec**: Sent to Anthropic API as-is
3. **API Key**: Used for authentication, never stored
4. **Results**: Displayed to user, not stored
5. **PII**: Masked before transmission, original not sent

### Third Party Services

- **Anthropic Claude AI**: Receives masked CV and job spec
- **Job URL Host**: Accessed to fetch job posting

### Data Retention

- **API Key**: Not retained (used only for request)
- **CV Content**: Not stored on our servers
- **Job Spec**: Not stored on our servers
- **Analysis Results**: Not stored (displayed only)

### User Rights

- ✅ Your data is not stored permanently
- ✅ PII is automatically protected
- ✅ API key is never logged
- ✅ Results are temporary (session only)

## Best Practices

### For Recruiters

1. **Initial Screening**: Use standard analysis
2. **Shortlist**: Use AI for top 10-20 candidates
3. **Documentation**: Save AI insights for interview prep
4. **Consistency**: Use same criteria for all candidates
5. **Budget**: Set monthly API usage limits

### For Job Seekers

1. **Test First**: Use standard analysis initially
2. **Optimize**: Use AI insights to improve CV
3. **Privacy**: Verify PII masking before sharing
4. **Cost**: Be aware of API costs if using own key
5. **Multiple Jobs**: Compare across different positions

### For HR Departments

1. **Policy**: Create guidelines for AI usage
2. **Training**: Train team on interpreting AI insights
3. **Auditing**: Review AI recommendations periodically
4. **Compliance**: Ensure GDPR/privacy compliance
5. **Backup**: Always have human review

## Compliance Notes

### GDPR Compliance

- ✅ PII is masked before external processing
- ✅ Data is not stored permanently
- ✅ User controls when AI is used
- ✅ Transparent about data usage

### Equal Opportunity

- ⚠️ AI recommendations are advisory only
- ⚠️ Final decisions must be human-made
- ⚠️ Use as one input among many
- ⚠️ Avoid over-reliance on AI scores

## Support

### Getting Help

1. **Check error message**: Often contains the solution
2. **Review this guide**: Common issues covered
3. **Test API key**: Try in Anthropic Console directly
4. **Check status**: Visit status.anthropic.com
5. **Review logs**: Check browser console (F12)

### Reporting Issues

When reporting problems, include:
- Error message (redact API key!)
- Steps to reproduce
- Browser and version
- CV file size and format
- Whether standard analysis works

## Future Enhancements

Planned features:
- 🔄 Batch AI analysis
- 🔄 Custom analysis prompts
- 🔄 AI-powered interview questions
- 🔄 Skill gap training recommendations
- 🔄 Comparison across multiple candidates
- 🔄 Export AI insights to PDF

---

**Remember**: AI analysis is a tool to assist decision-making, not replace human judgment. Always review AI recommendations critically and make final hiring decisions based on comprehensive evaluation.