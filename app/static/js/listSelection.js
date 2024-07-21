var checked_elements = [];
var list_objects = {};

// List Id herausfinden
const getListId = (obj) => {

    let list_id = $(obj).closest('div.list-js').attr('id')

    return list_id;
}

// List Objekt herausfinden
const getListObj = (obj) => {

    let list_id = $(obj).closest('div.list-js').attr('id')

    return list_objects[list_id];
}

// Holt die Id des List-Elements
function getListElementId(obj) {
    return $(obj).closest('tr.list_element').attr('data-id')
}

// Listelement auswählen
const selectListItem = (obj) => {

    let listObj = getListObj(obj),
        list_id = getListId(obj);

    if ($(obj).is(':checked')) {
        let list_item = listObj.get('id', getListElementId(obj))[0];
        list_item.values({
            selected: 'true'
        })
    } else {
        let list_item = listObj.get('id', getListElementId(obj))[0];
        list_item.values({
            selected: 'false'
        })
    }

    if (listObj.get('selected', 'true').length < listObj.items.length) {
        $('#' + list_id + ' .list-select-all').prop('checked', false)
    } else {
        $('#' + list_id + ' .list-select-all').prop('checked', true)
    }

    setCheckedElements(list_id, listObj)
    disableButtons(list_id)

}

// Alle Listenelemente auswählen
$('.list-select-all').change(function() {

    let listObj = getListObj(this),
        list_id = getListId(this);

    if ($(this).is(':checked')) {

        // Value selected auf true in der liste setzen
        $.each(listObj.matchingItems, function() {
            let list_item = this;
            list_item.values({
                selected: 'true'
            })
        })

        // Input checked setzen
        $.each($('#' + list_id + ' input.list-selection'), function(){
            $(this).prop('checked', true)
        })

    } else {

        // Value selected auf true in der liste setzen
        $.each(listObj.matchingItems, function() {
            let list_item = this;
            list_item.values({
                selected: 'false'
            })
        })

        $.each($('#' + list_id + ' input.list-selection'), function(){
            $(this).prop('checked', false)
        })

    }

    setCheckedElements(list_id, listObj)
    disableButtons(list_id)

})

// Array an ausgewählten Elementen
function setCheckedElements(list_id, listObj) {

    checked_elements = []

    let selected_items = listObj.get('selected', 'true')

    $.each(selected_items, function(){
        checked_elements.push(parseInt(this.values().id))
    })

    $('#' + list_id + ' .selection-amount span.selected').html(checked_elements.length)

}

// Maximal zur Verfügung stehende Elemente setzen
const setMaxListItems = (list_id, value) => {
    
    $('#' + list_id + ' .selection-amount span.total-amount').html(value)

}
const increaseMaxListItems = (list_id) => {
    
    let current_value = parseInt($('.selection-amount span.total-amount').html())
    $('#' + list_id + ' .selection-amount span.total-amount').html(current_value += 1)

}
const decreaseMaxListItems = (list_id) => {
    
    let current_value = parseInt($('.selection-amount span.total-amount').html())
    $('#' + list_id + ' .selection-amount span.total-amount').html(current_value -= 1)

}

// Buttons zur Verfügung stellen
function disableButtons(list_id) {

    if (checked_elements.length != 0) {
        $.each($('#' + list_id + ' .table-list-buttons button.list-selection-dependent:not(.save):not(.not-disabled)'), function(){
            $(this).attr('disabled', false)
        })
    } else {
        $.each($('#' + list_id + ' .table-list-buttons button.list-selection-dependent:not(.save):not(.not-disabled)'), function(){
            $(this).attr('disabled', true)
        })
    }

}

// Bei mehreren Seiten muss beim Seitenwechsel, falls select_all = True ist, alles ausgewählt werden
const pageClick = (obj) => {

    updateSelection(getListId(obj))

    if (typeof additionalPageClickFunktion == 'function') { 
        additionalPageClickFunktion(); 
    }
}

// Update selected on view
function updateSelection(list_id) {

    setTimeout(function() {
        $.each($('#' + list_id + ' input.list-selection'), function(){

            if ($(this).prev().html() == 'true') {
                $(this).prop('checked', true)
            } else {
                $(this).prop('checked', false)
            }
        })
            
    }, 50)

}

// Clear Selection
function clearSelection(list_id) {

    $('#' + list_id + ' .list-select-all').prop('checked', false)

    let listObj = list_objects[list_id];

    $.each(listObj.items, function() {
        let list_item = this;
        list_item.values({
            selected: 'false'
        })
    })

    $.each($('#' + list_id + ' input.list-selection'), function(){
        $(this).prop('checked', false)
    })

}



// Filterfunktion mit mehreren Filterelementen
var filter_values = [];
function filterList(listObj) {

    let response = true;

    filter_values = filter_values.filter(item => item.values.length != 0)

    if (filter_values.length == 0) {
        listObj.filter()
    } else {
        listObj.filter(function(item) {

            response = true

            for (let dict of filter_values) {

                let key = dict.key,
                    values = dict.values;

                if (typeof item.values()[key] == 'object') {

                    response = item.values()[key].some(element => values.includes(element))

                    if (!response) {
                        break;
                    }

                } else {

                    if (!values.includes(item.values()[key])) {
                        response = false;
                        break;
                    }
                }

            }

            return response;
        })
    }

    $('.amount-items').html(listObj.matchingItems.length)

}

// Seitenfunktion
function toFirstPage(obj) {

    let listObj = getListObj(obj),
        list_id = getListId(obj);

    // Gets first Page number from pagination list and click
    listObj.show(1, maxItems)

    updateSelection(list_id)
}

function toLastPage(obj) {

    let listObj = getListObj(obj),
        list_id = getListId(obj);

    // Gets last Page number from pagination list and click
    let list_amount = listObj.size(),
        max_pages = Math.ceil(list_amount / maxItems);
        max_pages -= 1
    
        listObj.show((max_pages * maxItems) + 1, maxItems)

    updateSelection(list_id)
}
