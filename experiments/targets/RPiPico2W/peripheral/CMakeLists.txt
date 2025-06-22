cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(picow_ble)

pico_sdk_init()



# From: <pico-sdk>/src/rp2_common/pico_btstack/CMakeLists.txt
# Make a GATT header file from a BTstack GATT file
# Pass the target library name library type and path to the GATT input file
# To add additional directories to the gatt #import path, add them to the end of the argument list.
function(pico_btstack_make_gatt_header TARGET_LIB TARGET_TYPE GATT_FILE)
        find_package (Python3 REQUIRED COMPONENTS Interpreter)
        get_filename_component(GATT_NAME "${GATT_FILE}" NAME_WE)
        get_filename_component(GATT_PATH "${GATT_FILE}" PATH)
        set(TARGET_GATT "${TARGET_LIB}_gatt_header")
        set(GATT_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated/${TARGET_GATT}")
        set(GATT_HEADER "${GATT_BINARY_DIR}/${GATT_NAME}.h")
        list(TRANSFORM ARGN PREPEND "-I")
        add_custom_target(${TARGET_GATT} DEPENDS ${GATT_HEADER})
        add_custom_command(
                OUTPUT ${GATT_HEADER}
                DEPENDS ${GATT_FILE}
                WORKING_DIRECTORY ${GATT_PATH}
                COMMAND ${CMAKE_COMMAND} -E make_directory ${GATT_BINARY_DIR} &&
                        ${Python3_EXECUTABLE} ${PICO_SDK_PATH}/lib/btstack/tool/compile_gatt.py ${GATT_FILE} ${GATT_HEADER} ${ARGN}
                VERBATIM)
        add_dependencies(${TARGET_LIB}
                ${TARGET_GATT}
                )
        target_include_directories(${TARGET_LIB} ${TARGET_TYPE}
                ${GATT_BINARY_DIR}
                )
endfunction()



add_executable(picow_ble_peripheral
    server.c server_common.c
)

target_link_libraries(picow_ble_peripheral
    pico_stdlib
    pico_btstack_ble
    pico_btstack_cyw43
    pico_cyw43_arch_none
)

target_include_directories(picow_ble_peripheral PRIVATE
    ${CMAKE_CURRENT_LIST_DIR} # For btstack config
)

pico_btstack_make_gatt_header(picow_ble_peripheral PRIVATE "${CMAKE_CURRENT_LIST_DIR}/lbs.gatt")
pico_add_extra_outputs(picow_ble_peripheral)
