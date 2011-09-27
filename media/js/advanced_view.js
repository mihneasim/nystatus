var rows = [];

function ChangelogRow(tr){
    // Properties
    this.j_tr = jQuery(tr);
    this.pk = parseInt(this.j_tr.attr("id").split('-')[1]);


    // Setting Event Handlers
    this.j_tr.find(".toggle_update_info").click(
        function(x){
            return function(){jQuery("#update_info-" + x.pk).toggle(500);};
      }(this)
    );

    this.j_tr.find(".toggle_changelog_info").click(
        function(x){
            return function(){jQuery("#changelog_info-" + x.pk).toggle(500);};
      }(this)
    );

}

function init_rows(){
    j_trs = jQuery("tr.changelog_row");
    for(var i=0; i<j_trs.length; i++)
      rows[i] = new ChangelogRow(j_trs[i]);
}

jQuery(document).ready(function(){
    init_rows();
});
