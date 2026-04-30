import streamlit as st, plotly.graph_objects as go

def render(results, weights, universe, add, remove):
    st.title("Gemini-like Momentum Portfolio")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Universe", len(universe))
    c2.metric("Added", len(add))
    c3.metric("Removed", len(remove))
    c4.metric("Final positions", int((weights.iloc[-1]>0).sum()))
    fig=go.Figure(); fig.add_trace(go.Scatter(y=results["equity"], name="Equity")); st.plotly_chart(fig, use_container_width=True)
    st.dataframe(weights.tail(10))
