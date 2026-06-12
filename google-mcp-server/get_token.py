from auth import get_credentials

if __name__ == "__main__":
    print("Starting Google OAuth flow...")
    try:
        creds = get_credentials()
        print("OAuth flow completed successfully!")
        print("token.json has been generated.")
    except Exception as e:
        print(f"Error during OAuth flow: {e}")
