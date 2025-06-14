import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier #import main model randF
import warnings
from sklearn.metrics import accuracy_score

warnings.filterwarnings('ignore')

# Load dataset
data = pd.read_csv('data2.csv')

x = data[["is_verified", "following_count", "followers_count", "is_default_profile_image"]] # features
y = data['is_spam_account'] #target

# Check for missing values and replace them with 0
x = x.fillna(0) 

# Split data
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)

# Hyperparameter tuning for Random Forest
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'class_weight': ['balanced']
}

rf = RandomForestClassifier(random_state=0)
grid_search = GridSearchCV(rf, param_grid, cv=3, n_jobs=-1, scoring='accuracy')
grid_search.fit(x_train, y_train)

# Best model selection
best_model = grid_search.best_estimator_
best_model.fit(x_train, y_train)

# Predictions and accuracy
y_pred = best_model.predict(x_test)
accuracy = accuracy_score(y_test, y_pred)
#print("Accuracy = ", accuracy)

import time
import re
import requests
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob


def get_sentiment(text):
    """Returns sentiment polarity (-1 to 1) rounded to int (-1, 0, 1)."""
    return int(np.sign(TextBlob(text).sentiment.polarity)) if text else 0

def extract_int(text): #to extract integer only
    #print(text)
    """Extracts and converts numbers from a text, including k (thousands) and M (millions)."""
    text = text.replace(",", "").lower()  # Remove commas and convert to lowercase
    match = re.search(r'(\d+\.?\d*)([km]?)', text)  # Match numbers with optional 'k' or 'm'
    #print(match)
    
    if match:
        number = float(match.group(1))  # Extract the numeric part
        suffix = match.group(2)  # Extract the suffix (if any)
        
        if suffix == 'k':
            return int(number * 1_000)
        elif suffix == 'm':
            return int(number * 1_000_000)
        else:
            return int(number)  # No suffix means it's a normal number

    return 0  # Default to 0 if no valid number is found


'''
**********************
CHANGE THE CREDENTIALS
**********************
'''

# Hardwired credentials
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"
EMAIL = "EMAILID"  # Replace with your email

def login_to_x(driver):
    """Logs into X.com securely, handling email verification if prompted."""
    driver.get("https://x.com/login")
    time.sleep(5)

    try:
        # Enter username
        username_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_input.send_keys(USERNAME)
        time.sleep(2)

        driver.find_element(By.XPATH, "//span[contains(text(),'Next')]").click()
        time.sleep(3)

        # Check if email input is required
        try:
            email_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            email_input.send_keys(EMAIL)
            time.sleep(2)
            driver.find_element(By.XPATH, "//span[contains(text(),'Next')]").click()
            time.sleep(3)
        except:
            print("No email verification required.")

        # Enter password
        password_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(PASSWORD)
        time.sleep(2)

        driver.find_element(By.XPATH, "//span[contains(text(),'Log in')]").click()
        time.sleep(5)

        print("✅ Login successful!")

    except Exception as e:
        print(f"❌ Login failed: {e}")


def get_x_user_details(username):
    """Fetches detailed user data from X.com after logging in, returning only a list of integers & boolean values."""
    url = f"https://x.com/{username}"

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.36 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        login_to_x(driver)

        driver.get(url)
        time.sleep(7)  

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✅ Profile page loaded!")
        except:
            return {"error": "Profile page failed to load."}

        # Extract data points
        is_verified = 0
        profile_description_sentiment = 0
        following_count = 0
        followers_count = 0
        is_default_profile_image = 0
        identical_tweet_freq = 0

        try:
            driver.find_element(By.CSS_SELECTOR, "svg[data-testid='icon-verified']")
            is_verified = 1
        except:
            pass

        try:
            bio = driver.find_element(By.CSS_SELECTOR, "div[data-testid='UserDescription']").text
            profile_description_sentiment = get_sentiment(bio)
        except:
            pass

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers') or contains(@href, '/following')]"))
            )
            stats = driver.find_elements(By.XPATH, "//a[contains(@href, '/followers') or contains(@href, '/following')]")

            for stat in stats:
                text = stat.text
                if "Followers" in text:
                    followers_count = extract_int(text)
                elif "Following" in text:
                    following_count = extract_int(text)
        except:
            print("⚠️ Followers/Following count not found!")

        try:
            tweets = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='tweetText']")
            tweet_texts = [tweet.text for tweet in tweets]

            if tweet_texts:
                unique_tweets = set(tweet_texts)
                identical_tweet_freq = (len(tweet_texts) - len(unique_tweets)) / len(tweet_texts)
            else:
                identical_tweet_freq = 0  # No tweets found

        except:
            print("⚠️ Could not fetch tweets properly.")
            identical_tweet_freq = 0  # Default to 0 if extraction fails

        try:
            followers_element = driver.find_element(By.XPATH, "//a[contains(@href, 'followers')]//span")

            followers_count = extract_int(followers_element.text)
        except:
            print("⚠️ Followers count not found!")
            followers_count = -1  # Assign -1 if extraction fails
  

        try:
            profile_img = driver.find_element(By.CSS_SELECTOR, "img[alt*='Image']")
            img_url = profile_img.get_attribute("src")
            if "default_profile_images" in img_url:
                is_default_profile_image = 1

            response = requests.head(img_url)
            if response.status_code != 200:
                is_profile_image_valid = 0
        except:
            pass

        if followers_count == 0 and following_count == 0:
            return {"error": "User not found or profile is private."}

        return [
            is_verified, profile_description_sentiment, following_count, followers_count,
            is_default_profile_image, identical_tweet_freq
        ]

    except Exception as e:
        return {"error": str(e)}

    finally:
        driver.quit()



def predict_values(a,username):
    yp=best_model.predict([[a[0],a[2],a[3],a[4]]])
    if yp[0]==1:
        result_text = f"'{username}' is likely a Bot!"
                # Define features and target variable
        data1=pd.read_csv("dataspam.csv")
        x = data1[["identical_tweet_freq"]]

        y = data1['is_spam_account']

        # Check for missing values and replace them with 0
        x = x.fillna(0)

        # Split data
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)

        from sklearn.linear_model import LogisticRegression
        model=LogisticRegression()
        model.fit(x_train,y_train)
        yp1=model.predict([[a[5]]])
        ypred1=model.predict(x_test)
        print("logistic =",accuracy_score(y_test,ypred1))
        if(yp1[0]==1):
            result_text = f"'{username}' is a Spam Bot!"
        else:
            print("the account is a normal bot")

    else :
        result_text = f"'{username}' seems like a Human User."

    return(result_text)

# user interface
import tkinter as tk
from tkinter import messagebox

def detect_bot():
    username = entry.get().strip()
    label.config(text=f"username: {username}")

    if not username:
      messagebox.showwarning("Input Error", "Please enter a username.")
      return
  
    label.config(text=f"username: {username}")
    details = get_x_user_details(username)
    print(details)
    result_text=predict_values(details,username)

    messagebox.showinfo("Result", result_text)
#  main
# Create main window
root = tk.Tk()
root.title("X Bot Detection")
root.geometry("600x350")
root.configure(bg="white")


# Styling
frame = tk.Frame(root, bg="white", padx=40, pady=40)
frame.pack(pady=50)

label = tk.Label(frame, text="Enter Username:", fg="black", bg="white", font=("Arial", 16,"bold"))
label.pack(pady=10)

entry = tk.Entry(frame, font=("Arial", 18), width=30, bd=2, relief="solid")
entry.pack(pady=10)

button = tk.Button(frame, text="Check", font=("Arial", 14, "bold"), bg="black", fg="white", padx=15, pady=8, command=detect_bot)
button.pack(pady=10)

# Run application
root.mainloop()




