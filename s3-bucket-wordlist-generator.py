print("Enter the brand names (comma-separated): ")

input_brands = input().strip()
brands = [b.strip() for b in input_brands.split(",") if b.strip()]

# Remove the line that was overwriting the brands list
# brands = []  # This line was clearing all the input!

core_keywords = [
    "assets", "static", "cdn", "media", "content",
    "public", "files", "resources", "downloads", "uploads",
    "images", "videos"
]

env_keywords = [
    "prod", "production", "stage", "staging",
    "dev", "development", "test", "qa", "sandbox", "uat"
]

region_keywords = [
    "us-east-1", "us-west-2", "eu-central-1",
    "ap-south-1", "global"
]

infra_keywords = [
    "logs", "audit-logs", "monitoring", "metrics",
    "telemetry", "build-artifacts", "deployments",
    "configs", "backups", "archives", "artifacts"
]

service_keywords = [
    "user-content", "user-uploads", "user-media",
    "customer-data", "partner-assets",
    "inventory-media", "checkout-static",
    "auth-logs", "api-content",
    "ml-models", "analytics-data"
]

output = set()

def combine(parts):
    """Combine list elements into a hyphen-separated string."""
    return "-".join(parts)

for brand in brands:
    # 1. brand + core
    for k in core_keywords:
        output.add(combine([brand, k]))

    # 2. brand + env
    for e in env_keywords:
        output.add(combine([brand, e]))

    # 3. brand + env + core
    for e in env_keywords:
        for k in core_keywords:
            output.add(combine([brand, e, k]))

    # 4. brand + region
    for r in region_keywords:
        output.add(combine([brand, r]))

    # 5. brand + region + core (fixed indentation)
    for r in region_keywords:
        for k in core_keywords:
            output.add(combine([brand, r, k]))

    # 6. brand + infra
    for i in infra_keywords:
        output.add(combine([brand, i]))

    # 7. brand + env + infra
    for e in env_keywords:
        for i in infra_keywords:
            output.add(combine([brand, e, i]))

    # 8. brand + service
    for s in service_keywords:
        output.add(combine([brand, s]))

# Write to file
with open("s3_wordlist.txt", "w") as f:
    for item in sorted(output):
        f.write(item + "\n")

print(f"Generated {len(output)} combinations.")
print("Saved to s3_wordlist.txt")