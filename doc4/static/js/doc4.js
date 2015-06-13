function showHide(elt){
    var elem = document.getElementById(elt);
    
    if (elem.style.display == 'block') {
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';
    }
}
