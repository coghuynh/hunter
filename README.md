# Hunter

Candidate Recommendation System for IT hiring, helping HR quickly find top matches using AI.


## Overview

Hunter is an AI-powered recommendation system that connects HR teams with the most suitable candidates.  
It uses graph-based data modeling and smart search/ranking algorithms to simplify candidate discovery.

## Features
- Parse and store resumes into structured graph database.
- Link candidates with skills, projects, degrees, and languages.
- REST API for integration with external HR tools.
- Easy extension with new features and ranking strategies.

## Installation / Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/your-org/hunter.git
   cd hunter
2. Set up `env.hunter`

   ```bash
   docker build -t hunter:1.0 .
   docker-compose up -d
## License
Licensed under the Apache License, Version 2.0 – see the [LICENSE](LICENSE) file for details.

