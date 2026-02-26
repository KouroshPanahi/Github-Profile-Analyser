# Contributing to GitHub Profile Analyzer

Thank you for considering contributing to GitHub Profile Analyzer.

## Code of Conduct

This project follows the Contributor Covenant Code of Conduct. By participating, you agree to maintain a respectful environment.

## Getting Started

1. Fork the repository
2. Clone your fork:

``` bash
git clone https://github.com/YOUR-USERNAME/Github-Profile-Analyser.git
cd Github-Profile-Analyser
```

3. Set up virtual environment:
``` bash
python -m venv venv
source venv/bin/activate (On Windows: venv\Scripts\activate)
```
4. Install dependencies:
```bash
pip install -r requirements.txt
```
5. Set GitHub token:
6. Run the application:
```bash
python main.py
```

## How Can I Contribute

### Reporting Bugs
- Check existing issues first
- Use a clear title and description
- Provide steps to reproduce
- Include expected vs actual behavior
- Add screenshots if helpful
- Mention your OS and Python version

### Suggesting Features
- Use a descriptive title
- Explain why it's useful
- Describe how it should work
- Include examples if possible

### Your First Contribution
Look for issues labeled:
good first issue (For beginners)
help wanted (Needs assistance)
bug (Something broken)
enhancement (New features)

## Pull Request Process

1. Update your fork with latest changes:
```bash
git remote add upstream https://github.com/KouroshPanahi/Github-Profile-Analyser.git
git fetch upstream
git checkout main
git merge upstream/main
```

2. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes
4. Test your changes
5. Commit with clear message:
```bash
git commit -m "type: description"
```

6. Push to your fork:
``` bash
git push origin your-branch-name
```

7. Open a Pull Request to the main branch

### Pull Request Requirements
- Focus on one issue or feature
- No merge conflicts
- Update documentation if needed
- Pass all tests

## Style Guidelines

### Python
- Use 4 spaces for indentation
- Max line length: 79 characters
- Import order: standard library, third-party, local
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants


### HTML/CSS
- Use semantic HTML5 elements
- Indent with 2 spaces
- Use lowercase for tags and attributes
- Include alt text for images
- Use meaningful class names

### Git Commit Messages

Format: type: description

Types:
feat: New feature
fix: Bug fix
docs: Documentation
style: Code formatting
refactor: Code restructuring
perf: Performance improvement
test: Adding tests
chore: Maintenance

## Recognition

Contributors will be mentioned in the README.

Ready to contribute? Fork and submit a pull request.

Questions? Open an issue or tag @KouroshPanahi.