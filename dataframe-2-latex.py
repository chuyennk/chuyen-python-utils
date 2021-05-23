import pandas as pd
import re
from lxml import etree
from io import StringIO

def dataframe2latex(df, caption=None, column_format = None):
    r""" 
    Convert a python dataframe to latex longtable string.

    Args:
        df (dataframe): source to convert to latex
        caption (string, optional): caption to display in latex
        column_format (string): to specify the columns format for latex table, 
            i.e. '|p{0.2\linewidth}|p{0.8\linewidth}' for 2 columns

    Returns:
        string: the latex longtable string
        
    Notes:
        This function using df.to_latex() as the base to convert a dataframe to latex string.
            However, it allow a few basic html tags (i.e. <b>, <u>, <i>, <p> and <table>) to be used in dataframe.
        This function need latex doc to \usepackage{longtable} and \usepackage{booktabs}
    """

    with pd.option_context("max_colwidth", None):
        strhtml = df.to_latex(longtable=True, index=False, escape=False, caption=caption, column_format=column_format)
    
    # read the latex string as html to parse and convert to latex tags    
    parser = etree.HTMLParser()
    tree   = etree.parse(StringIO(strhtml.replace(r'\n','')), parser) # expects a file, use StringIO for string
    root = tree.getroot()
    
    def loophtml(el):
        result = []
        
        if (el.text):
            result.append(el.text.strip())
            
        #for each type of html elements, convert them to correspondent latex tag
        for idx, subEl in enumerate(el):
            if ((subEl.tag in ['p']) & (idx > 0)): #ignore the first <p> which is inserted by etree
                result.append(f'\\newline {loophtml(subEl)} \\newline')
            elif (subEl.tag in ['br']):
                result.append(f'\\newline ')
            elif (subEl.tag in ["b"]):
                result.append(f'\\textbf{{{loophtml(subEl)}}} ')
            elif (subEl.tag in ['i']):
                result.append(f'\\textit{{{loophtml(subEl)}}} ')
            elif (subEl.tag in ['u']):
                result.append(f'\\underline{{{loophtml(subEl)}}} ')
            elif (subEl.tag in ['table']):
                if len(subEl)>0:
                    colFormat = 'l'*len(subEl[0])
                    result.append(f'\\newline \n\\begin{{tabular}}{{{colFormat}}} {loophtml(subEl)} \n\\bottomrule \n\\end{{tabular}} \\newline')
                else:
                    result.append('got an incomplete table here')
            elif ((subEl.tag =='tr') & (idx==0)):
                result.append(f'\n\\toprule \n{loophtml(subEl)} \\\\ \n\\midrule ')
            elif ((subEl.tag =='tr') & (idx<len(el)-1)):
                result.append(f'\n{loophtml(subEl)} \\\\ \\midrule ')
            elif ((subEl.tag =='tr') & (idx==len(el)-1)):
                result.append(f'\n{loophtml(subEl)} \\\\')
            elif ((subEl.tag in ['td', 'th']) & (idx==0)):
                result.append(f'{loophtml(subEl)} ')
            elif ((subEl.tag in ['td','th']) & (idx>0)):
                result.append(f' & {loophtml(subEl)} ')
            else:
                result.append(loophtml(subEl))

            if (subEl.tail):
                result.append(subEl.tail.strip())
            
        return ' '.join(result)
    
    str = loophtml(root) #loop thru html and replace with latex tags
    str = re.sub("  +"," ",str) #replace those with more than 2 whitespace with only 1 space
    str = str.replace(' \\\\\n ', '\\\\ \midrule\n') #insert a boderline for each row by puting \midrule
    return str


# example:
df = pd.read_csv('Book2.csv')
strlatex = dataframe2latex(df, caption='My Chrono Table', column_format='p{0.2\\textwidth}|p{0.2\\textwidth}|p{0.8\\textwidth}')
print(strlatex)
