"""Shopper-needs map derived from reviewed baseline views."""
from .render import esc, fmt
from .export import view_key


def atlas(data):
    cfg=data['study']; main=cfg['layers'][0]['id']; focal=cfg['focal_brand']
    tiles=[]
    for question in cfg['questions']:
        if question['kind']!='discovery': continue
        q=question['id']; view=data['views'][view_key(main,'baseline','question',q,'all')]
        values=[row['first_choice_credit_sum'] for row in view['rows']]
        maximum=max(values,default=0)
        winners=[row['brand'] for row in view['rows'] if row['first_choice_credit_sum']==maximum and maximum>0]
        focal_credit=next((row['first_choice_credit_sum'] for row in view['rows'] if row['brand']==focal),0)
        winner=' / '.join(winners) if winners else 'No overall lead'
        cls=' focal-lead' if focal in winners else ''
        tiles.append('<a class="atlas-need'+cls+'" href="#needs" data-route="explore" data-preset-question="'+esc(q)+'"><span class="atlas-question">'+esc(data['labels'][q])+'</span><strong>'+esc(winner)+'</strong><span class="atlas-count">'+(fmt(maximum)+' / '+str(view['n'])+' first-choice credit' if winners else 'No brand receives first-choice credit')+'</span><span class="atlas-foot">'+esc(focal)+': '+fmt(focal_credit)+' / '+str(view['n'])+'<br>No overall lead: '+str(view['no_lead_n'])+' / '+str(view['n'])+'</span><span class="atlas-open">Compare answers ↗</span></a>')
    return '<section id="category-map" class="category-atlas"><div class="section-heading"><span>Discovery map</span><h2>Who leads each shopper need?</h2></div><p class="caption">Baseline main sample, all engines. Each tile names the brand(s) with the highest overall first-choice credit, including ties. The no-overall-lead count is separate and can exceed an individual brand. Select a need to open its full comparison and evidence.</p><div class="atlas-grid">'+''.join(tiles)+'</div><p class="caption">Discovery prompts only. Counts describe this prompt set; they are not market shares. Highlighted rules identify needs where '+esc(focal)+' shares or holds the lead.</p></section>'
