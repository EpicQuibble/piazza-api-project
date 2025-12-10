#!/usr/bin/env python3
"""
Piazza Poll Auto-Responder
Automatically monitors and responds to polls in a Piazza class

Requirements:
    pip install piazza-api

Usage:
    python piazza_poll_bot.py
"""

import time
import random
from piazza_api import Piazza
from piazza_api.rpc import PiazzaRPC
from datetime import datetime
import config as cfg
import json

class PiazzaPollBot:
    def __init__(self, email, password, class_id, poll_answer_index=0, check_interval=60):
        """
        Initialize the Piazza Poll Bot
        
        Args:
            email: Your Piazza email
            password: Your Piazza password
            class_id: The class ID (e.g., 'jx7ab2cd4ef')
            poll_answer_index: Which option to select (0 = first option, 1 = second, etc.)
            check_interval: How often to check for new polls (in seconds)
        """
        self.email = email
        self.password = password
        self.class_id = class_id
        self.poll_answer_index = poll_answer_index
        self.check_interval = check_interval
        self.answered_polls = set()
        self.piazza = Piazza()
        self.rpc = None
        self.network = None
        
    def login(self):
        """Login to Piazza"""
        try:
            print(f"[{self._timestamp()}] Logging in to Piazza...")
            # Login with the high-level API
            self.piazza.user_login(email=self.email, password=self.password)
            self.network = self.piazza.network(self.class_id)
            
            # Create RPC instance and share the session
            self.rpc = PiazzaRPC(self.class_id)
            # Share the session cookies between Piazza and RPC
            self.rpc.session = self.network._rpc.session
            
            # Set browser-like user agent to avoid detection
            self.rpc.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
            })
            
            print(f"[{self._timestamp()}] Successfully logged in!")
            return True
        except Exception as e:
            print(f"[{self._timestamp()}] Login failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _timestamp(self):
        """Get current timestamp for logging"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_all_posts(self):
        """Retrieve all posts from the class"""
        try:
            # Use the feed endpoint instead of iter_all_posts to avoid rate limiting
            # The feed gives us all posts in one request instead of fetching each individually
            feed = self.network.get_feed(limit=10, offset=0)
            post_ids = [post['id'] for post in feed.get('feed', [])]
            
            print(f"[{self._timestamp()}] Found {len(post_ids)} posts in feed")
            
            # Fetch full details for each post, but with rate limiting protection
            posts = []
            for i, post_id in enumerate(post_ids):
                try:
                    # Add small delay between requests to avoid "too fast" error
                    if i >= 0:  # Don't delay before first request
                        time.sleep(random.uniform(0.7, 0.9))  # 700-900ms between posts
                    
                    post = self.network.get_post(post_id)
                    posts.append(post)
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'too fast' in error_msg or 'wait' in error_msg:
                        # Hit rate limit, wait longer and retry
                        print(f"[{self._timestamp()}] Rate limit hit, waiting 2 seconds...")
                        time.sleep(2)
                        try:
                            post = self.network.get_post(post_id)
                            posts.append(post)
                        except:
                            print(f"[{self._timestamp()}] Could not fetch post {post_id} after retry, skipping")
                    else:
                        print(f"[{self._timestamp()}] Error fetching post {post_id}: {str(e)[:100]}")
            
            return posts
        except Exception as e:
            print(f"[{self._timestamp()}] Error fetching posts: {e}")
            return []
    
    def is_poll(self, post):
        """Check if a post is a poll"""
        try:
            # Check if post type is 'poll'
            if post.get('type') == 'poll':
                return True
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] Error checking if post is poll: {e}")
            return False
    
    def get_poll_details(self, post_id):
        """Fetch full poll details using get_post to get complete data"""
        try:
            return self.network.get_post(post_id)
        except Exception as e:
            print(f"[{self._timestamp()}] Error fetching full post details: {e}")
            return None
    
    def is_poll_open(self, post):
        """Check if a poll is still open for responses"""
        try:
            # Check status field
            if post.get('status') != 'active':
                return False
            
            # Check config for poll_is_closed flag
            config = post.get('config', {})
            if config.get('poll_is_closed') == 1:
                return False
            
            return True
            
        except Exception as e:
            print(f"[{self._timestamp()}] Error checking if poll is open: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def has_answered_poll(self, post):
        """Check if we've already answered this poll"""
        return post['id'] in self.answered_polls
    
    def has_user_voted(self, post):
        """Check if the current user has already voted in the poll"""
        try:
            # Check in data field for has_voted list
            data = post.get('data', {})
            if data:
                has_voted = data.get('has_voted', [])
                if has_voted and len(has_voted) > 0:
                    return True
            
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] Error checking if user voted: {e}")
            return False
    
    def get_poll_options(self, post):
        """Extract poll options from post structure"""
        try:
            # Options are in questions[0]['answers']
            if 'questions' in post and len(post['questions']) > 0:
                question = post['questions'][0]
                if 'answers' in question:
                    return question['answers']
            return None
        except Exception as e:
            print(f"[{self._timestamp()}] Error getting poll options: {e}")
            return None
    
    def answer_poll(self, post):
        """Answer a poll using the correct API method"""
        try:
            post_id = post['id']
            subject = post['history'][0].get('subject', 'Untitled Poll')
            
            print(f"\n[{self._timestamp()}] ==========================================")
            print(f"[{self._timestamp()}] Attempting to answer poll: {subject}")
            print(f"[{self._timestamp()}] Post ID: {post_id}")
            
            # Get poll options
            options = self.get_poll_options(post)
            
            if not options:
                print(f"[{self._timestamp()}] Error: Could not find poll options")
                self.answered_polls.add(post_id)
                return False
            
            # Filter out deleted options
            active_options = [opt for opt in options if not opt.get('deleted', False)]
            
            if not active_options:
                print(f"[{self._timestamp()}] Error: No active options found")
                self.answered_polls.add(post_id)
                return False
            
            # Select the option (use modulo to handle index out of range)
            selected_index = self.poll_answer_index % len(active_options)
            selected_option = active_options[selected_index]
            selected_id = selected_option['id']
            selected_text = selected_option['text']
            
            print(f"[{self._timestamp()}] Available options:")
            for i, opt in enumerate(active_options):
                marker = " <-- SELECTING THIS" if i == selected_index else ""
                print(f"[{self._timestamp()}]   [{i}] {opt['text']} (ID: {opt['id']}){marker}")
            
            # Use the correct API format discovered from browser network inspection
            print(f"[{self._timestamp()}] Submitting vote using content.vote API...")
            
            # Add human-like delay before voting (2-5 seconds)
            delay = random.uniform(2, 5)
            print(f"[{self._timestamp()}] Waiting {delay:.1f} seconds before submitting (human-like delay)...")
            time.sleep(delay)
            
            try:
                response = self.rpc.request(
                    method="content.vote",
                    data={
                        "cid": post_id,
                        "votes": [selected_id]  # votes is plural and an array!
                    }
                )
                
                # Check if response indicates success
                if response.get('error') is None:
                    print(f"[{self._timestamp()}] !!!!!!!!!!!! Poll answered !!!!!!!!!!!!")
                    print(f"[{self._timestamp()}] Selected option: {selected_text} (ID: {selected_id})")
                    
                    # Show vote results
                    result = response.get('result', {})
                    total_votes = result.get('total_votes', 'unknown')
                    print(f"[{self._timestamp()}] Total votes on this poll: {total_votes}")
                    print(f"[{self._timestamp()}] Response: {json.dumps(response, indent=2)[:500]}")
                    
                    self.answered_polls.add(post_id)
                    print(f"[{self._timestamp()}] ==========================================\n")
                    return True
                else:
                    error = response.get('error', 'Unknown error')
                    print(f"[{self._timestamp()}] ✗ Failed: {error}")
                    
                    # Check if already voted
                    if 'already' in str(error).lower() or 'voted' in str(error).lower():
                        print(f"[{self._timestamp()}] Marking as answered (already voted)")
                        self.answered_polls.add(post_id)
                    
                    print(f"[{self._timestamp()}] ==========================================\n")
                    return False
                    
            except Exception as e:
                error_msg = str(e).lower()
                print(f"[{self._timestamp()}] ✗ Exception: {str(e)[:300]}")
                
                # Check if error indicates already voted or closed
                if any(word in error_msg for word in ['already', 'voted', 'closed', 'expired']):
                    print(f"[{self._timestamp()}] Marking as answered (already voted or closed)")
                    self.answered_polls.add(post_id)
                
                print(f"[{self._timestamp()}] ==========================================\n")
                return False
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"[{self._timestamp()}] Unexpected error answering poll {post_id}: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if error indicates poll is closed or already voted
            if any(word in error_msg for word in ['closed', 'expired', 'not accept', 'already voted', 'already answered']):
                print(f"[{self._timestamp()}] Marking poll as answered (closed or already voted)")
                self.answered_polls.add(post_id)
            
            return False
    
    def check_for_polls(self):
        """Check for new polls and answer them"""
        print(f"[{self._timestamp()}] Checking for new polls...")
        
        posts = self.get_all_posts()
        print(f"[{self._timestamp()}] Total posts retrieved: {len(posts)}")
        
        polls_found = 0
        new_polls_found = 0
        closed_polls_skipped = 0
        already_answered = 0
        already_voted = 0
        
        for post in posts:
            if self.is_poll(post):
                polls_found += 1
                post_id = post['id']
                subject = post['history'][0].get('subject', 'Untitled')
                
                print(f"\n[{self._timestamp()}] Found poll #{polls_found}: {subject} (ID: {post_id})")
                
                # Check status and config
                status = post.get('status', 'unknown')
                config = post.get('config', {})
                poll_is_closed = config.get('poll_is_closed', 0)
                
                print(f"[{self._timestamp()}]   Status: {status}, poll_is_closed: {poll_is_closed}")
                
                if self.has_answered_poll(post):
                    print(f"[{self._timestamp()}]   -> Already in answered list, skipping")
                    already_answered += 1
                    continue
                
                # Check if user has already voted
                if self.has_user_voted(post):
                    print(f"[{self._timestamp()}]   -> User has already voted, skipping")
                    self.answered_polls.add(post['id'])
                    already_voted += 1
                    continue
                
                # Check if poll is still open
                if not self.is_poll_open(post):
                    print(f"[{self._timestamp()}]   -> Poll is closed, skipping")
                    self.answered_polls.add(post['id'])
                    closed_polls_skipped += 1
                    continue
                
                print(f"[{self._timestamp()}]   -> This is a new, open poll! Attempting to answer...")
                new_polls_found += 1
                self.answer_poll(post)
                
                # Add random delay between polls to seem more human
                if new_polls_found > 0:
                    inter_poll_delay = random.uniform(2, 5)
                    print(f"[{self._timestamp()}] Waiting {inter_poll_delay:.1f}s before checking next poll...")
                    time.sleep(inter_poll_delay)
        
        print(f"\n[{self._timestamp()}] Summary:")
        print(f"[{self._timestamp()}]   Total polls found: {polls_found}")
        print(f"[{self._timestamp()}]   New polls to answer: {new_polls_found}")
        print(f"[{self._timestamp()}]   Already in answered list: {already_answered}")
        print(f"[{self._timestamp()}]   Already voted: {already_voted}")
        print(f"[{self._timestamp()}]   Closed polls: {closed_polls_skipped}")
        
        return new_polls_found
    
    def run(self):
        """Main loop - continuously monitor for polls"""
        if not self.login():
            print("Failed to login. Exiting.")
            return
        
        print(f"\n{'='*60}")
        print(f"Piazza Poll Bot Started")
        print(f"Class ID: {self.class_id}")
        print(f"Auto-selecting option index: {self.poll_answer_index}")
        print(f"Check interval: {self.check_interval} seconds")
        print(f"{'='*60}\n")
        
        try:
            while True:
                self.check_for_polls()
                
                # Randomize check interval to avoid perfect timing patterns
                # Use base interval +/- 25% random variation
                variation = self.check_interval * 0.25
                randomized_interval = self.check_interval + random.uniform(-variation, variation)
                
                print(f"[{self._timestamp()}] Waiting {randomized_interval:.1f} seconds before next check...")
                print(f"[{self._timestamp()}] (Base: {self.check_interval}s, Randomized: {randomized_interval:.1f}s)\n")
                time.sleep(randomized_interval)
                
        except KeyboardInterrupt:
            print(f"\n[{self._timestamp()}] Bot stopped by user.")
        except Exception as e:
            print(f"\n[{self._timestamp()}] Unexpected error: {e}")


if __name__ == "__main__":
    # Create and run the bot
    bot = PiazzaPollBot(
        email=cfg.EMAIL,
        password=cfg.PASSWORD,
        class_id=cfg.CLASS_ID,
        poll_answer_index=cfg.POLL_ANSWER_INDEX,
        check_interval=cfg.CHECK_INTERVAL
    )
    
    bot.run()