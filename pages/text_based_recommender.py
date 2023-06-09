


"""
 UPDATE Apr 18: corrected typos 

"""

# import libraries
import streamlit as st
import pandas as pd
import numpy as np
from scipy import sparse
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt

import warnings
warnings.filterwarnings('ignore',category=DeprecationWarning)
pd.set_option('display.max_columns', 100)
RANDOM_STATE= 42

from collections import Counter
from wordcloud import WordCloud, STOPWORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import re
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('averaged_perceptron_tagger')
nltk.download('vader_lexicon')

from nltk import word_tokenize, pos_tag
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer,PorterStemmer
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer

########################################################################################################
# basic settings #

# set pages
st.set_page_config(
    page_title = 'Multippage App',
    page_icon='👋'
)

st.title('AirBnb Rentals in Seattle')

# header
st.header(':blue[Try the text based recommender]')
st.caption('(Note: This recommender only uses the text from the fields: listing_name, description, host_name, host_location, host_about, host_response_time, host_neighbourhood, host_verifications, neighbourhood_cleansed, neighbourhood_group_cleansed, neighborhood_overview, property_type, room_type, and amenities)')

##########################################################################################################
# prepare data #

# get price-filterred listing data
@st.cache_data
def get_data(price_range):

    # directly load the saved dataset
    df = pd.read_pickle('data/data_cleaned/cleaned_listing_finalized_for_streamlit.zip')
    # # select cols
    listing_cols = ['listing_id','listing_url','price',
                    'beds', 'bedrooms','bathrooms_count',
                    'number_of_reviews','review_scores_rating', 'polarity',
                    'comments', 'comments_nouns_adjs']
    # get content cols
    content_cols = ['listing_name', 'description',
                    'host_name', 'host_location', 'host_about',
                    'host_response_time', 'host_neighbourhood',
                    'host_verifications', 'neighbourhood_cleansed',
                    'neighbourhood_group_cleansed','neighborhood_overview',
                    'property_type', 'room_type','amenities',
                    'content','cleaned_content'
                   ]
    df = df.loc[:,[*listing_cols, *content_cols]]

    # filter df by price range
    if len(df.loc[(df['price']>price_range[0])&(df['price']<=price_range[1])])!=0:
        df_filter = df.loc[(df['price']>=price_range[0])&(df['price']<=price_range[1])]
    else:
        df_filter = df
        st.info('There are no listings within your preferred price range.\n Recommendations will be made purely based on your input query and rental text description(or try a new price range instead).')
    return df_filter

# make a price query slider
st.write(":green[Choose your preferred price range]")
st.caption("(Note: Default price range is (50,5000), without changing, all recommendations will be based on your plain text input query.)")
price_range = st.slider(" ",value = [50,5000])
st.write("Your default price range:", price_range)

# make an input box
st.subheader(":green[Describe the rental you're looking for]")
defult_input = "I want a private room close to uw campus with parking and coffee shop."
input_query = st.text_input(" ",defult_input)
submit = st.button('Submit')

## get final filtered dataframe 
df_rec = get_data(price_range)

##########################################################################################################
# code to get top 5 recommendations #
# prepare stopword set
added_stopwords = ["can't",'t', 'us', 'say','would', 'also','within','stay', 'since']
nltk_STOPWORDS = set(stopwords.words("english"))
nltk_STOPWORDS.update(added_stopwords)

# preprocess input query
@st.cache_data
def preprocess_text(text, stopwords = nltk_STOPWORDS, stem=False, lemma=False):
    # clean the text
    text = text.lower()
    # remove html and all other sybols
    text = re.sub("(<.*?>)|([^0-9A-Za-z \t])","",text)
    text = re.sub("(br)", '', text)
    # tokenize the text
    text = word_tokenize(text)
    # remove stopwords and non alpha words
    text = [word for word in text if word not in stopwords]
    # get the root of word
    if stem == True:
        stemmer = PorterStemmer()
        text = [stemmer.stem(word) for word in text]
    # normalize the word
    if lemma == True:
        lemmatizer = WordNetLemmatizer()
        text = [lemmatizer.lemmatize(word) for word in text]
    # list to string
    text = ' '.join(text)
    return text

# Vectorize data
@st.cache_data
def vectorize_data(corpus):
    # TfidfVectorizer
    tfidf_vectorizer = TfidfVectorizer(
                                    ngram_range = (1,2),
                                    stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
    return tfidf_vectorizer, tfidf_matrix

# get corpus
corpus = df_rec['content'].values
tfidf_vectorizer, tfidf_matrix = vectorize_data(corpus)

# extract best similarity indices
@st.cache_data
def extract_best_indices(similarity, top_n, mask=None):
    """
    Use sum of the cosine distance over all tokens ans return best mathes.
    m (np.array): cos matrix of shape (nb_in_tokens, nb_dict_tokens)
    topk (int): number of indices to return (from high to lowest in order)
    """
    # return the sum on all tokens of consine for the input query
    if len(similarity.shape) > 1:
        cos_sim = np.mean(similarity, axis=0)
    else:
        cos_sim = similarity
    index = np.argsort(cos_sim)[::-1]

    if mask is not None:
        assert mask.shape == similarity.shape
        mask = mask[index]
    else:
        mask = np.ones(len(cos_sim))
    mask = np.logical_or(cos_sim[index] != 0, mask) #eliminate 0 cosine distance
    best_index = index[mask][:top_n]
    return best_index

# get recommendations
@st.cache_data
def get_recommendations(df,input_query, _tfidf_matrix, n=5):
    # reset df index to avoid no-index error 
    df = df.reset_index()
    # embed input query
    tokens = preprocess_text(input_query,stopwords = nltk_STOPWORDS, stem=False, lemma=True).split()
    query_vector = tfidf_vectorizer.transform(tokens)
    # get similarity
    tfidf_matrix_sparse = sparse.csr_matrix(_tfidf_matrix)
    similarity = cosine_similarity(query_vector, tfidf_matrix_sparse)
    # similarity = cosine_similarity(query_vector, _tfidf_matrix)

    # best cosine distance for each token independantly
    best_index = extract_best_indices(similarity, top_n=n)

    # return the top n similar listings
    result_df = df.loc[best_index,:]
    result_df = result_df.loc[:, ['listing_id', 'listing_url','listing_name', 'description',
                                 'price','beds', 'bedrooms','bathrooms_count','room_type','property_type',
                                 'neighborhood_overview', 'neighbourhood_cleansed', 'neighbourhood_group_cleansed',
                                 'host_about', 'amenities', 'number_of_reviews', 'review_scores_rating']]
    result_df = result_df.reset_index().iloc[:,1:]
    result_df.index = np.arange(1,len(result_df)+1)

    return result_df

# Try the recommender system
recomended_listings = get_recommendations(df_rec, input_query, tfidf_matrix, n=5)

st.header(':blue[Top 5 recommended rentals]')
st.write(recomended_listings)

########################################################################################################
# add rental review sentiment trends plot for the recommended listing #

@st.cache_data
def get_review_data():
    # directly read the saved cleaned_review_with_polarity dataset
    review_df = pd.read_pickle('data/data_cleaned/cleaned_review_with_polarity_and_topic.zip')
    return review_df
review_df = get_review_data()

# make plot
# notice: altair can only take <=5000 rows, so cannot show all listings at once
@st.cache_data
def plot_listing_sentiment_over_time(df,listing_id = None):
    # prepare dataframe
    sub_df = df[df['listing_id'].isin(listing_id)]
    # map recommended rentals to listing_id
    dict_map = dict(zip(listing_id,['1st_rec','2nd_rec','3rd_rec','4th_rec','5th_rec'])) 
    sub_df['recommended_listings'] = sub_df['listing_id'].map(dict_map)

    if sub_df.shape[0] != 0:
        base = alt.Chart(sub_df).encode(
            x='year(date):T',
            y='mean(polarity)',
            color=alt.Color('recommended_listings:O', scale=alt.Scale(scheme= 'dark2')))

        plot = alt.layer(base.mark_line() + base.mark_circle(size=100)
                        ).properties(
                            width = 500,
                            height= 350,
                         ).interactive()

        st.altair_chart(plot, use_container_width=True)
    else:
        st.info("Oops, there is no relevant review data (before Dec 24, 2022), then no graph to show here.")

# write a note
st.header(':blue[Rental review sentiment trends]')
st.caption("(Note: No graph to show if the rental doesn't have any comments.)")

# plot the figure
rec_listing_ids = recomended_listings['listing_id'].values
plot_listing_sentiment_over_time(review_df, rec_listing_ids)

########################################################################################################
# add rental description wordcloud #

@st.cache_data
def make_wordcloud(df, col, listing_id, stop_words, mask=None):

    if listing_id in df['listing_id'].values:
        text = df[df['listing_id'] == listing_id][col].values[0]
        if type(text) == str:
            wordcloud = WordCloud(width = 100,
                        height = 100,
                        stopwords=stop_words,
                        scale=10,
                        colormap = 'PuRd',
                        background_color ='black',
#                       mask = None,
                        max_words=100,
                        ).generate(text)

            fig, ax = plt.subplots(figsize=(4,4))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            plt.show()
            st.pyplot(fig)
        else:
            if 'comment' in col:
                st.info('Oops, this listing currently has no comments.')
            else:
                st.info('Oops, this listing currently has no descriptions.')

# generate wordcloud for a recommended listing
st.header(':blue[Rental description WordCloud]')
st.subheader(':green[Pick a top n recommendation for more info]')
st.caption("(Note: the first listing id is the first recommended listing (the most relevant), and the second listing id is the second recommended rental, and so on.)")

# get a top n listing id from the user
selected_listing_id = st.selectbox("Choose listing id:", recomended_listings['listing_id'])
index = recomended_listings['listing_id'].tolist().index(selected_listing_id)
link = recomended_listings.listing_url.tolist()[index]

# Show name and URL of selected property
st.write("\"{}\" - [{}]({})".format(recomended_listings.listing_name.tolist()[index],link,link))

# Draw the word cloud
wordcloud_STOPWORDS = STOPWORDS
make_wordcloud(df_rec,'cleaned_content', selected_listing_id, wordcloud_STOPWORDS, mask=None)

########################################################################################################
# add rental review wordcloud #

# generate review wordcloud
st.header(':blue[Rental review WordCloud]')

# Show name and URL of selected property
st.write("\"{}\" - [{}]({})".format(recomended_listings.listing_name.tolist()[index],link,link))

# Draw the word cloud
make_wordcloud(df_rec,'comments_nouns_adjs', selected_listing_id, wordcloud_STOPWORDS, mask=None)

########################################################################################################
##### add rental review topic bar chart #####

# make review topic bar chart
@st.cache_data
def plot_listing_review_topics(df, col, listing_id):

    if listing_id in df['listing_id'].values:
        sub_df = df[df['listing_id'] == listing_id]
        plot = alt.Chart(sub_df).mark_bar().encode(
                        y=alt.Y('review_topic_interpreted:O', sort='-x', axis=alt.Axis(labelLimit=200,labelFontSize=14)),
                        x='count():Q',
                        color=alt.Color('listing_id:O', scale=alt.Scale(scheme= 'dark2'))
                    ).properties(
                        width=400,
                        height=300
                    ).interactive()
        st.altair_chart(plot, use_container_width=True)
    else:
        st.info("Oops, this listing currently has no comments.")

# generate review report for a recommended listing (has comments)
st.header(':blue[Rental review topics BarChart]')

# Show name and URL of selected property
st.write("\"{}\" - [{}]({})".format(recomended_listings.listing_name.tolist()[index],link,link))

# Draw the topic bar chart
plot_listing_review_topics(review_df,'review_topic_interpreted', selected_listing_id)

########################################################################################################
# add rental review report (negative review sentences) #
@st.cache_data
def get_review_sentiment_report(df,col,listing_id):
    sorted_neg_sentences = np.nan
    if listing_id in df['listing_id'].values:
        comments = df[df['listing_id'] == listing_id]['comments'].values[0]
        if len(comments) <=1:
            st.info('Oops, this listing currently has no comments.')
        else:
            # segement all comments into sentences for the given listing
            review_sentences = df[df['listing_id'] == listing_id]['comments'].apply(lambda x: re.sub("(<.*?>)|([\t\r])","",x)).str.split('[.?!]').values.tolist()[0]
            review_sentences = [sentence for sentence in review_sentences if sentence]
            num_review_sentences = len(review_sentences)

            # get polarity score for the positives sentences in all the comments
            neg_sentences = []
            for i, text in enumerate(review_sentences):
                sid_obj = SentimentIntensityAnalyzer().polarity_scores(text)
                if (sid_obj['neg'] > 0.2) & (sid_obj['compound'] < -0.1):
                    neg_sentences.append((sid_obj['compound'],sid_obj['neg'],review_sentences[i]))
                else:
                    pass

            neg_percent = (len(neg_sentences)/num_review_sentences)
            non_neg_percent = 1-neg_percent
            # sort the negative sentences first by 'compund' score (ascending order) then by 'neg' score (descending order)
            sorted_neg_sentences = [comment for score1, score2, comment in sorted(neg_sentences, key=lambda x: (x[0], -x[1]))]

            st.subheader(":green[Overall:]")
            st.write("{}% of all the reviews sentences ({}/{}) on Airbnb for this listing are not negative!".format(round(non_neg_percent*100,2), num_review_sentences-len(neg_sentences),num_review_sentences))
            st.write("{}% of them ({}/{}) are estimated to be negative review sentences.".format(round(neg_percent*100,2),len(neg_sentences),num_review_sentences))

            st.subheader(":green[Potentially helpful negative review sentences:]")
            st.caption("(Note: some of the negative review sentences might not sound negative to you due to the prediction algorithm used in our model. However, those review sentences are already the most negative ones in all the comments about this rental.)")

            if len(sorted_neg_sentences) >0:
                for i, sentence in enumerate(sorted_neg_sentences):
                    st.write("{}: {}".format(i+1, sentence))
            else:
                st.write("Wow, this listing currently doesn't have any estimated negative sentences!")
        return sorted_neg_sentences



# generate review report for a recommended listing (has comments)
st.header(':blue[Rental review report]')

# Show name and URL of selected property
st.write("\"{}\" - [{}]({})".format(recomended_listings.listing_name.tolist()[index],link,link))

# Return the report
sorted_neg_sentences = get_review_sentiment_report(df_rec,'comments',selected_listing_id)
