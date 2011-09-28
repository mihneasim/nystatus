var tips_register = function (manual){
    if (manual==undefined)
      manual = false;
    var trigger = manual ? 'manual' : 'hover';
    var gravity = 'e';
    for(i=0; i<tipdict.length; i++){
        if(!tipdict[i].gravity)
          gravity = 'e';
        else
          gravity = tipdict[i].gravity;
        jQuery(tipdict[i].id).tipsy({ trigger: trigger,
                                     fade: true, gravity: gravity, html: true,
                                     title: tipdict[i].title});
    }
  };

jQuery(document).ready(function(){ tips_register(); });
