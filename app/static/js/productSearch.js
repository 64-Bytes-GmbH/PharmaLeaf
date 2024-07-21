var scriptTag = document.querySelector('script[src*="productSearch.js"]')
var productUrl = scriptTag.getAttribute('data-product-url')

const $searchContainer = $('.searchProductContainer');
var $dropdownDiv = $('.dropdownProductList');
let debounceTimer;

$searchContainer.find('.searchProductInput').on('input', function() {
    
    // Get type of search input
    const searchType = $(this).data('search-type')

    clearTimeout(debounceTimer)

    debounceTimer = setTimeout(() => {
        performSearch($(this), searchType)
    }, 300)
});

function performSearch($input, searchType) {

    const searchWord = $input.val().trim();

    // Check if searchWord is empty
    if (searchWord.length === 0) {
        return;
    }

    $.ajax({
        type: 'POST',
        url: productUrl,
        traditional: true,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        },
        data: {
            'searchWord': 'searchWord',
            'search': searchWord,
        },
        success: (data) => {

            // Get width from searchContainer if $input attr dropdown-width is not set
            var width = $input.outerWidth();

            if ($input.attr('dropdown-width')) {
                width = $input.attr('dropdown-width');
            }

            // Get max-heigth from $input attr dropdown-max-height
            const maxInnerHeight = $input.attr('dropdown-max-height');

            // Get top and left position from $input
            const top = $input.offset().top + $input.outerHeight();
            const left = $input.offset().left;

            // Create dropdown div element if not exists else use existing element and empty it and set styles
            if ($('.dropdownProductList').length == 0) {
                $dropdownDiv = $('<div>', {
                    'class': 'dropdownProductList overflow-y-auto absolute bg-white divide-y divide-gray-100 rounded-lg shadow-xl dark:bg-gray-800 dark:divide-gray-700',
                    'aria-labelledby': 'dropdownNotificationButton',
                    'style': `top: ${top}px; left: ${left}px; width: ${width}px; max-height: ${maxInnerHeight}px; z-index: 1000;`
                });
            } else {
                $dropdownDiv = $('.dropdownProductList');
                $dropdownDiv.empty();

                // Set styles
                $dropdownDiv.css('top', top + 'px');
                $dropdownDiv.css('left', left + 'px');
                $dropdownDiv.css('width', width + 'px');
                $dropdownDiv.css('max-height', maxInnerHeight + 'px');

            }

            var $innerDiv = $('<div>', {
                'class': 'divide-y divide-gray-100 dark:divide-gray-700'
            });

            $dropdownDiv.append($innerDiv);

            // Einfügen des DIV-Elements in den HTML-Code
            $('body').append($dropdownDiv);

            for (const item of data.items) {
                let status_class = getStatusClass(item.status);
                let template = createProductTemplate(item, status_class, searchType);
                $innerDiv.append(template);
            }
        },
        error: () => {
            toggleModal('alert-modal');
        }
    });
}

function getStatusClass(status) {
    if (status === '3' || status === '2') return 'text-green-500';
    if (status === '1') return 'text-yellow-500';
    return 'text-red-700 dark:text-red-500';
}

function createProductTemplate(item, status_class, searchType) {
    return `<a href="javascript:void(0)" data-${searchType}="${item.name}" data-product-id=${item.id} class="flex px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700">
        <div class="w-full ps-3">
            <div class="flex flex-row mb-1">
                <div class="text-sm font-semibold text-gray-900 dark:text-white">
                    ${item.name}
                </div>
                <div class="text-sm ml-auto font-semibold ${status_class} ${searchType === 'global-search-product' ? 'hidden' : ''}">
                    ${item.status_display}
                </div>
            </div>
            <div class="text-sm text-blue-600 dark:text-blue-400">
                ${item.cultivar} | THC: ${item.thc_value} | CBD ${item.cbd_value}
            </div>
        </div>
    </a>`;
}

$(document).on('click', '[data-global-search-product]', function() {
    updateUrlParameters('search_product', $(this).data('global-search-product'));
});

$(document).on('click', '[data-add-product-search]', function() {
    addProduct($(this).data('product-id'));
});

$(document).on('click', '[data-import-order-search-product]', function() {

    const product = $(this).data('import-order-search-product');

    var index = document.getElementById('extractedOrderedProductList').children.length;
    
    const productListContainer = document.getElementById('extractedOrderedProductList');

    const productDiv = document.createElement('div')
    productDiv.className = "imported-product-container bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"
    productDiv.id = `orderProduct-${index}`

    // Inhalt für das Produkt-Div
    const contentHtml = `
        <div class="flex gap-4 md:gap-6 mb-3">
            <div class="mt-2" style="flex: 4">
                <label for="product-${index}" class="inline-flex items-center mb-2 text-sm font-medium text-gray-900 dark:text-white">
                    Produkt
                </label>
                <input id="product-${index}" name="product" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500" value="${product}">
            </div>
            <div class="mt-2" style="flex: 2">
                <label for="productAmount-${index}" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Menge</label>
                <input type="number" name="productAmount" id="productAmount-${index}" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500" value="10">
            </div>
            <div class="inline-flex rounded-md shadow-sm" role="group" style="flex: 1; height: 42px; margin-top: auto;">
                <a href="javascript:void(0)" onclick="reduceAmountImportedProduct(${index})" type="button" class="inline-flex items-center px-4 py-2.5 text-sm font-medium text-gray-300 bg-transparent border border-gray-900 rounded-s-lg hover:bg-gray-900 hover:text-white focus:z-10 focus:ring-2 focus:ring-gray-500 focus:bg-gray-900 focus:text-white dark:border-white dark:text-white dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700 dark:focus:bg-gray-700">
                    <svg class="w-4 h-4 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 8">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 5.326 5.7a.909.909 0 0 0 1.348 0L13 1"/>
                    </svg>
                </a>
                <a href="javascript:void(0)" onclick="increaseAmountImportedProduct(${index})" type="button" class="inline-flex items-center px-4 py-2.5 text-sm font-medium text-gray-300 bg-transparent border border-gray-900 rounded-e-lg hover:bg-gray-900 hover:text-white focus:z-10 focus:ring-2 focus:ring-gray-500 focus:bg-gray-900 focus:text-white dark:border-white dark:text-white dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700 dark:focus:bg-gray-700">
                    <svg class="w-4 h-4 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 8">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7 7.674 1.3a.91.91 0 0 0-1.348 0L1 7"/>
                    </svg>
                </a>
            </div>

            <button style="position: absolute; right: 30px;" type="button" onclick="removeImportedProduct(event)" data-modal-target="product-delete-popup-modal" data-modal-toggle="product-delete-popup-modal" class="remove-imported-product-btn text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto mb-auto inline-flex dark:hover:bg-gray-600 dark:hover:text-white">
                <svg aria-hidden="true" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>                                    
                </svg>
                <span class="sr-only">Produkt löschen</span>                                
            </button>
        </div>
    `;

    // Setze den HTML-Inhalt des Produkt-Divs
    productDiv.innerHTML = contentHtml

    // Füge das Produkt-Div dem Container hinzu
    productListContainer.appendChild(productDiv)

});

$searchContainer.find('.searchProductInput').on('focus blur', function(event) {

    setTimeout(() => {
        if (event.type === 'blur') $dropdownDiv.remove();

        if (event.type === 'focus') {
            if (this.value.length > 0) {
                performSearch($(this), $(this).data('search-type'));
            }
        };
    }, 200);

});