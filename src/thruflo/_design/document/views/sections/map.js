/*
  
  First split for Setext_ ``H1``s:
  
      Heading 1
      =========
  
  Then for Setext_ ``H2``s:
  
      Heading 2
      ---------
  
  Then for atx_ ``H1`` to ``H6``s:
  
      # Heading 1
      # Heading 1 #
      ...
      ###### Heading 6
      ###### Heading 6 ######
  
  .. _Setext: http://docutils.sourceforge.net/mirror/setext.html
  .. _atx: http://www.aaronsw.com/2002/atx/
  
  
*/
/*
  
  Then yield rows so that:
  
      Example Document
      ================
      
      Lorum ipsum foo bar dolores.  Yaddy yadda.  Intro text.
      
      ## Sections
      
      ### Section 1
      
      This is section one ...
      
      ### Section Two
      
      section two ...
      
      Footer
      ------
      
      &copy; thruflo.'
  
  Becomes:
  
      [["Example Document", [], [], 3 more...], "Lorum ipsum ..."]
      [["Example Document", "Sections", [], 3 more...], ""]
      [["Example Document", "Sections", "Section 1", 3 more...], "This is section one ..."]
      [["Example Document", "Sections", "Section Two", 3 more...], "section two ..."]
      [["Example Document", "Footer", [], 3 more...], "&copy; thruflo."]
  
  
*/
function (doc) {
  if (doc.doc_type == 'Document') {
    var i = 0;
    var parts = doc.content.replace(
      /^(.+)[ \t]*\n=+[ \t]*\n/gm,
      function (wholeMatch, m1) {
        return "<h1>h1:" + m1 + "</h1>"
      }
    ).replace(
      /^(.+)[ \t]*\n-+[ \t]*\n/gm,
      function (wholeMatch, m1) {
        return "<h2>h2:" + m1 + "</h2>"
      }
    ).replace(
      /^(\#{1,6})[ \t]*(.+?)[ \t]*\#*\n/gm,
      function (wholeMatch, m1, m2) {
        var h_level = m1.length;
        return "<h" + h_level + ">h" + h_level + ":" + m2 + "</h" + h_level + ">"
      }
    ).split(/^<h[1-6]>(.+)<\/h[1-6]>[ \t]*\n/gm);
    while (true) {
      if (parts[i].indexOf('h') === 0) {
        break;
      }
      else {
        i++;
      }
    };
    parts = parts.slice(i); 
    var heading_parts,
        level,
        i_pos,
        h_pos,
        j,
        h,
        key = [0, null, 0, null, 0, null, 0, null, 0, null, 0, null],
        l = key.length,
        value;
    for (i = 0; i < parts.length; i = i + 2) {
      heading_parts = parts[i].split(':');
      level = parseInt(heading_parts[0][1]);
      h = heading_parts[1];
      h_pos = (level * 2) - 1;
      i_pos = h_pos - 1;
      key[i_pos] = i;
      key[h_pos] = h;
      for (j = h_pos + 1; j < l; j = j + 2) {
        if (key[j] != 0) {
          key[j] = 0;
          key[j + 1] = null;
        }
        else {
          break;
        }
      }
      value = parts[i + 1];
      emit(key.slice(0), value);
    }
  };
};