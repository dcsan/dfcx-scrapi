from lib.data.biglib import BigLib
import plotly.graph_objects as go
import numpy as np
import pandas as pd


class Sankey:

    @classmethod
    def query_paths(cls, use_case=None, where="\n", sprint=22, limit=2000):
        print('use_case', use_case)

        if use_case:
            where = f"{where} \n AND use_case = '{use_case}' "
        # else:
        #     options = 'and use_case is NULL '

        if sprint:
            where += f"\n AND current_sprint_number = {sprint} "

        qs = f'''SELECT
            page_source as source,
            page_target as target,
            count(*) as value

            FROM `nj-pods-dev.scoobi.chat_logs`
            WHERE
                page_target is not NULL
                AND page_source is not NULL
                AND
                    {where}

            group by
                page_source, page_target

            order by value desc

            LIMIT {limit}
        '''
        print(qs)
        df = BigLib.query_df(qs)
        return df

    @classmethod
    def draw_one(cls, use_case=None, set_name=None, limit=50, sprint=None, where="", fname=None):
        where = f'dataset_display_name = "{set_name}" '
        df = Sankey.query_paths(
            use_case=use_case, limit=limit, sprint=sprint, where=where)
        # remove self cycles
        # cycles = df[df.source == df.target].index
        # df = df.drop(cycles)

        fname = f"sp_{sprint}_{set_name}_{use_case}"
        # fname = fname or f'{where}-{use_case}-s{sprint}-d{limit}'
        base_path = f'./data/ignored/sankeys/{fname}'

        img_path = f'{base_path}.png'
        html_path = f'{base_path}.html'
        title = f'{where} | use_case: {use_case} | sprint: {sprint} | limit: {limit}'

        links = df.to_dict('records')

        df = pd.DataFrame(links)
        names = np.unique(df[["source", "target"]], axis=None)
        nodes = pd.Series(index=names, data=range(len(names)))
        # df['label'] = nodes.index

        print('nodes\n', nodes)
        print('df\n', df.head(50))

        fig = go.Figure(
            go.Sankey(
                # node={"label": df['label']},
                node={"label": nodes.index},
                arrangement='snap',
                link={
                    "source": nodes.loc[df["source"]],
                    "target": nodes.loc[df["target"]],
                    "value": df["value"],
                    # "label": df["value"]
                },
            )
        )

        fig.update_layout(
            title_text=title,
            font_size=14,
            width=1920,
            height=1080
        )

        print('render to:', img_path)
        fig.write_image(img_path)
        fig.write_html(file=html_path)
        fig.show()
        return fig
