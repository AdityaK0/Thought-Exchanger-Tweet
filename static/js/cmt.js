function toggleCommentCard(event) {
  const tweetId = event.target.getAttribute('data-tweet-id');
  const commentCard = document.getElementById(`commentCard-${tweetId}`);
  const currentDisplay = commentCard.style.display;

  // Toggle the display property to show or hide the comment card for that tweet
  if (currentDisplay === 'none' || currentDisplay === '') {
    commentCard.style.display = 'block';
  } else {
    commentCard.style.display = 'none';
  }
}

