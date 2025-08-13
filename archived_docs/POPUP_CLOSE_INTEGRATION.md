# Popup Close Integration Guide

## Problem
When users click the X button in the vendor widget, it closes the widget but leaves the popup window open, requiring users to click the popup's X button as well.

## Solution
The vendor widget now sends a message to the parent popup window when the user clicks its X button. The popup needs to listen for this message and close itself.

## Implementation for WordPress Developer

### Option 1: Message-Based Closing (Recommended)
Add this JavaScript to your popup implementation:

```javascript
// Listen for close messages from the vendor widget
window.addEventListener('message', function(event) {
    // Security check - only accept messages from your domain
    if (event.origin !== 'https://dockside.life') {
        return;
    }
    
    // Handle close popup request from vendor widget
    if (event.data && event.data.type === 'closePopup' && event.data.source === 'vendorWidget') {
        // Close the popup window
        closePopup(); // Replace with your actual popup close function
        
        // OR if using a modal library, something like:
        // $('#your-modal').modal('hide');
        // $('.popup-overlay').fadeOut();
        // document.querySelector('.popup').style.display = 'none';
    }
});
```

### Option 2: Direct Window Close
If your popup is a separate window (not a modal), add this to the popup's JavaScript:

```javascript
// Allow the iframe to close the popup window
window.closeModal = function() {
    window.close();
};
```

### Option 3: Remove Widget X Button (Alternative)
If you prefer to only have the popup's close button, you can hide the widget's X button by adding this CSS to your popup:

```css
.close-button {
    display: none !important;
}
```

## Testing
After implementation:
1. Open the popup with the vendor widget
2. Click the X button inside the widget
3. Confirm the confirmation dialog
4. Both the widget and popup should close

## Popular Popup Library Examples

### For jQuery Modal
```javascript
window.addEventListener('message', function(event) {
    if (event.origin === 'https://dockside.life' && 
        event.data?.type === 'closePopup') {
        $('#vendor-popup-modal').modal('hide');
    }
});
```

### For Fancybox
```javascript
window.addEventListener('message', function(event) {
    if (event.origin === 'https://dockside.life' && 
        event.data?.type === 'closePopup') {
        $.fancybox.close();
    }
});
```

### For Elementor Popup
```javascript
window.addEventListener('message', function(event) {
    if (event.origin === 'https://dockside.life' && 
        event.data?.type === 'closePopup') {
        elementorFrontend.modules.popup.closePopup({}, event);
    }
});
```

## Fallback
The widget tries multiple methods to close the popup:
1. Sends a postMessage to the parent
2. Tries to call `window.parent.close()`  
3. Tries to call `window.parent.closeModal()`

If none work, the widget will still close but the popup will remain open (current behavior).